from odoo import api, models
import logging
import re
import traceback
from markupsafe import Markup

_logger = logging.getLogger(__name__)

class WhatsappDiscussMixin(models.AbstractModel):
    _name = 'whatsapp.logger'
    _description = 'WhatsApp Discuss Logger'

    def _coerce_partner(self, partner):
        """Return a single res.partner record from various input types."""
        try:
            _logger.info(f"=== COERCING PARTNER ===")
            _logger.info(f"Partner type: {type(partner)}")
            _logger.info(f"Partner value: {partner}")
            
            Partner = self.env['res.partner'].sudo()
            if not partner:
                _logger.error("Partner not provided")
                raise ValueError('Partner not provided')
                
            if hasattr(partner, 'ids'):
                _logger.info("Partner has 'ids' attribute, treating as recordset")
                partner = partner.sudo()
                if not partner:
                    _logger.error("Partner recordset is empty")
                    raise ValueError('Partner record does not exist')
                _logger.info(f"Returning first partner from recordset: {partner[0].name} (ID: {partner[0].id})")
                return partner[0]
                
            if isinstance(partner, int):
                _logger.info(f"Partner is integer ID: {partner}")
                rec = Partner.browse(partner)
                if not rec.exists():
                    _logger.error(f"Partner with ID {partner} does not exist")
                    raise ValueError(f'Partner id {partner} does not exist')
                _logger.info(f"Found partner by ID: {rec.name} (ID: {rec.id})")
                return rec
                
            if isinstance(partner, dict) and partner.get('id'):
                _logger.info(f"Partner is dict with ID: {partner.get('id')}")
                rec = Partner.browse(int(partner['id']))
                if not rec.exists():
                    _logger.error(f"Partner with ID {partner['id']} does not exist")
                    raise ValueError(f"Partner id {partner['id']} does not exist")
                _logger.info(f"Found partner by dict ID: {rec.name} (ID: {rec.id})")
                return rec
                
            _logger.error(f"Unsupported partner type: {type(partner)}")
            raise ValueError(f'Unsupported partner type: {type(partner)}')
            
        except Exception as e:
            _logger.error(f"=== PARTNER COERCION ERROR ===")
            _logger.error(f"Error coercing partner: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Partner value: {partner}")
            _logger.error(f"Partner type: {type(partner)}")
            raise

    @api.model
    def _ensure_partner_channel(self, partner, assign_user=True):
        """Ensure there is a private chat channel with the partner (customer).
        - assign_user=True: include current user as agent (for outgoing messages).
        - assign_user=False: only add customer + agent group (for incoming messages).
        """
        try:
            _logger.info("🟢 === ENSURING PARTNER CHANNEL ===")
            _logger.info(f"🧩 Partner: {partner}")
            _logger.info(f"🧩 Assign user: {assign_user}")
            _logger.info(f"👤 Current user: {self.env.user.name} (ID: {self.env.user.id})")

            partner = self._coerce_partner(partner)
            _logger.info(f"👥 Coerced partner: {partner.name} (ID: {partner.id})")

            Channel = self.env['discuss.channel'].sudo()

            # Reuse existing WhatsApp channel if found
            _logger.info("🔍 Searching for existing WhatsApp channel...")
            existing = Channel.search([
                ('channel_type', '=', 'channel'),
                ('wa_customer_partner_id', '=', partner.id),
                ('is_whatsapp', '=', True),
            ], limit=1)

            if existing:
                _logger.info(f"✅ Found existing channel: {existing[0].name} (ID: {existing[0].id})")
                _logger.info(f"👥 Channel members: {[m.name for m in existing[0].channel_partner_ids]}")
                return existing[0]

            _logger.info("🆕 No existing channel found, creating new one...")

            # Collect agent partners (from configured users in first active WhatsApp account)
            try:
                _logger.info("👨‍💻 Getting WhatsApp default agent users from WhatsApp Account...")
                wa_account = self.env['whatsapp.account'].sudo().search([], limit=1)
                agent_partners = wa_account.notify_user_ids.mapped('partner_id') if wa_account else self.env['res.partner']
                
                # Fallback to current user if no agents configured
                if not agent_partners and self.env.user and self.env.user.id != self.env.ref("base.public_user").id:
                     _logger.info("No agents configured in WhatsApp Account, adding current user as agent fallback")
                     # Logic below already adds current user, so we can leave agent_partners empty
                
                _logger.info(f"✅ Selected {len(agent_partners)} agent partners from WhatsApp Account: {[p.name for p in agent_partners]}")
            except Exception as e:
                _logger.warning(f"⚠️ Error getting default agent users from WhatsApp Account: {str(e)}")
                agent_partners = self.env['res.partner']

            # Build participant list
            partner_ids = [partner.id] + agent_partners.ids
            _logger.info(f"🧩 Base participant IDs: {partner_ids}")

            # Add current user (if not public user)
            if assign_user and self.env.user and self.env.user.id != self.env.ref("base.public_user").id:
                partner_ids.append(self.env.user.partner_id.id)
                _logger.info(
                    f"🙋 Added current user: {self.env.user.partner_id.name} (ID: {self.env.user.partner_id.id})")

            final_partner_ids = list(set(partner_ids))
            _logger.info(f"🧩 Final participant IDs: {final_partner_ids}")

            # Create channel (Odoo auto-creates members from channel_partner_ids)
            channel_vals = {
                'active': True,
                'name': partner.name,
                'display_name': partner.name,
                'channel_type': 'channel',
                'group_public_id': False,
                'wa_customer_partner_id': partner.id,
                'wa_user_partner_id': self.env.user.partner_id.id if assign_user else False,
                'is_whatsapp': True,
                'channel_partner_ids': [(4, pid) for pid in final_partner_ids],
            }

            _logger.info(f"⚙️ Creating channel with values: {channel_vals}")
            ch = Channel.create(channel_vals)
            _logger.info(f"✅ Created new channel: {ch.name} (ID: {ch.id})")

            # Remove public user if auto-subscribed
            try:
                public_partner = self.env.ref("base.public_user").partner_id
                if public_partner in ch.channel_partner_ids:
                    _logger.info("🧹 Removing public user from channel...")
                    ch.write({'channel_partner_ids': [(3, public_partner.id)]})
                    _logger.info("✅ Public user removed successfully")
            except Exception as e:
                _logger.warning(f"⚠️ Error removing public user: {str(e)}")

            # Broadcast to participants
            try:
                _logger.info(f"📢 Broadcasting to participants: {final_partner_ids}")
                ch._broadcast(set(final_partner_ids))
                _logger.info("✅ Broadcast completed")
            except Exception as e:
                _logger.warning(f"❌ Error broadcasting to participants: {str(e)}")

            _logger.info(f"🎯 Channel creation completed: {ch.name} (ID: {ch.id})")
            return ch

        except Exception as e:
            _logger.error("❌ === CHANNEL CREATION ERROR ===")
            _logger.error(f"❌ Error ensuring partner channel: {str(e)}")
            _logger.error(f"📜 Traceback: {traceback.format_exc()}")
            _logger.error(f"👥 Partner: {partner}")
            _logger.error(f"🧩 Assign user: {assign_user}")
            raise

    @api.model
    def log_to_channel(self, partner, body, fingerprint, is_incoming=True, attachment_ids=None, origin_model=None, origin_res_id=None, origin_name=None):
        """Log a WhatsApp message (incoming or outgoing) into Discuss for this partner.
        If origin_model/origin_res_id are provided, append a link back to the originating record.
        """
        try:
            _logger.info(f"=== LOGGING TO CHANNEL ===")
            _logger.info(f"Partner: {partner}")
            _logger.info(f"Body: {body[:100]}...")
            _logger.info(f"Fingerprint: {fingerprint}")
            _logger.info(f"Is incoming: {is_incoming}")
            _logger.info(f"Origin model: {origin_model}")
            _logger.info(f"Origin res_id: {origin_res_id}")
            _logger.info(f"Origin name: {origin_name}")
            _logger.info(f"Attachment IDs: {attachment_ids}")
            
            partner = self._coerce_partner(partner)
            _logger.info(f"Coerced partner: {partner.name} (ID: {partner.id})")
            
            channel = self._ensure_partner_channel(partner, assign_user=True)
            _logger.info(f"Channel: {channel.name} (ID: {channel.id})")
            
            MailMessage = self.env['mail.message'].sudo()

            # Avoid duplicates by fingerprint (message_id field)
            _logger.info("Checking for duplicate messages...")
            existing = MailMessage.search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
                ('message_id', '=', fingerprint),
            ], limit=1)
            
            if existing:
                _logger.info(f"Duplicate message found, returning existing: {existing.id}")
                return existing

            author_id = partner.id if is_incoming else self.env.user.partner_id.id
            _logger.info(f"Author ID: {author_id} ({'partner' if is_incoming else 'current user'})")

            # Build origin link html if provided
            origin_html = ''
            try:
                if origin_model and origin_res_id:
                    _logger.info(f"Building origin link for {origin_model} ID {origin_res_id}")
                    display_name = origin_name
                    if not display_name:
                        try:
                            rec = self.env[origin_model].sudo().browse(origin_res_id)
                            if rec.exists():
                                # name_get returns list of tuples
                                display_name = rec.display_name or (rec.name if hasattr(rec, 'name') else str(origin_res_id))
                                _logger.info(f"Retrieved display name: {display_name}")
                            else:
                                display_name = str(origin_res_id)
                                _logger.warning(f"Record does not exist, using ID: {display_name}")
                        except Exception as e:
                            _logger.warning(f"Error getting display name: {str(e)}")
                            display_name = str(origin_res_id)
                    
                    # Use Odoo webclient hash URL to open record form
                    link = f"/web#id={origin_res_id}&model={origin_model}&view_type=form"
                    origin_html = f"<br/><small>From {origin_model}: <a href=\"{link}\">{display_name}</a></small>"
                    _logger.info(f"Generated origin HTML: {origin_html}")
                else:
                    _logger.info("No origin model/res_id provided, skipping origin link")
            except Exception as e:
                _logger.warning(f"Failed to build origin link: {e}")
                _logger.warning(f"Traceback: {traceback.format_exc()}")
                origin_html = ''

            full_body = body or ''
            if origin_html:
                full_body = f"{full_body}{origin_html}"
                _logger.info(f"Combined body with origin link: {full_body[:200]}...")

            # Mark as HTML-safe so it renders anchor tags
            full_body_safe = Markup(full_body)
            _logger.info("Body marked as HTML-safe")

            # Post the message
            post_kwargs = {
                'body': full_body_safe,
                'message_type': 'comment',
                'subtype_xmlid': 'mail.mt_comment',
                'message_id': fingerprint,
                'author_id': author_id,
                'attachment_ids': attachment_ids or [],
            }
            
            _logger.info(f"Posting message with kwargs: {post_kwargs}")
            result = channel.message_post(**post_kwargs)
            _logger.info(f"Message posted successfully: {result}")
            return result
            
        except Exception as e:
            _logger.error(f"=== CHANNEL LOGGING ERROR ===")
            _logger.error(f"Error logging to channel: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Partner: {partner}")
            _logger.error(f"Body: {body}")
            _logger.error(f"Fingerprint: {fingerprint}")
            _logger.error(f"Is incoming: {is_incoming}")
            raise

    @api.model
    def log_incoming_if_exists(self, partner, body, fingerprint, context_id=None):
        """Post an incoming message to an existing 1:1 chat channel for partner.
        - Returns True if posted, False otherwise
        - Sets parent_id to the specific outgoing WA message we're replying to using context_id
        """
        try:
            _logger.info(f"=== LOGGING INCOMING MESSAGE ===")
            _logger.info(f"Partner: {partner}")
            _logger.info(f"Body: {body[:100]}...")
            _logger.info(f"Fingerprint: {fingerprint}")
            _logger.info(f"Context ID: {context_id}")
            
            partner = self._coerce_partner(partner)
            _logger.info(f"Coerced partner: {partner.name} (ID: {partner.id})")
            
            channel = self._ensure_partner_channel(partner, assign_user=False)
            _logger.info(f"Channel: {channel.name} (ID: {channel.id})")

            MailMessage = self.env['mail.message'].sudo()
            
            # Check for duplicates
            _logger.info("Checking for duplicate messages...")
            dup = MailMessage.search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
                ('message_id', '=', fingerprint),
            ], limit=1)
            
            if dup:
                _logger.info(f"Duplicate message found, skipping: {dup.id}")
                return False

            # Find the specific parent message we're replying to using context_id
            parent_msg = False
            if context_id:
                _logger.info(f"Looking for parent message with context_id: {context_id}")
                try:
                    # Look for the exact message we sent that this is a reply to
                    parent_msg = MailMessage.search([
                        ('model', '=', 'discuss.channel'),
                        ('res_id', '=', channel.id),
                        ('message_id', '=', f"wa:{context_id}"),
                    ], limit=1)
                    if parent_msg:
                        _logger.info(f"Found parent message for reply: context_id={context_id}, parent_id={parent_msg.id}")
                    else:
                        _logger.warning(f"No parent message found for context_id={context_id} in channel {channel.id}")
                except Exception as e:
                    _logger.warning(f"Could not find parent message with context_id {context_id}: {str(e)}")
                    _logger.warning(f"Traceback: {traceback.format_exc()}")
            else:
                _logger.info("No context_id provided, will use fallback parent message")
            
            # Fallback: if no context_id or parent not found, use last outgoing WA message
            if not parent_msg:
                _logger.info("Using fallback parent message search...")
                try:
                    user_partner_id = self.env.user.partner_id.id
                    _logger.info(f"Searching for last outgoing WA message by user partner ID: {user_partner_id}")
                    parent_msg = MailMessage.search([
                        ('model', '=', 'discuss.channel'),
                        ('res_id', '=', channel.id),
                        ('message_id', 'like', 'wa:%'),
                        ('author_id', '=', user_partner_id),
                    ], order='id desc', limit=1)
                    if parent_msg:
                        _logger.info(f"Using fallback parent message: parent_id={parent_msg.id}")
                    else:
                        _logger.warning(f"No fallback parent message found in channel {channel.id}")
                except Exception as e:
                    _logger.warning(f"Could not find fallback parent message: {str(e)}")
                    _logger.warning(f"Traceback: {traceback.format_exc()}")
                    parent_msg = False

            # Post the message
            post_kwargs = {
                'body': body,
                'message_type': 'comment',
                'subtype_xmlid': 'mail.mt_comment',
                'message_id': fingerprint,
                'author_id': partner.id,
                'parent_id': parent_msg.id if parent_msg else False,
            }
            
            _logger.info(f"Posting incoming message with kwargs: {post_kwargs}")
            result = channel.message_post(**post_kwargs)
            _logger.info(f"Incoming message posted successfully: {result}")
            return True
            
        except Exception as e:
            _logger.error(f"=== INCOMING MESSAGE LOGGING ERROR ===")
            _logger.error(f"log_incoming_if_exists failed: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Partner: {partner}")
            _logger.error(f"Body: {body}")
            _logger.error(f"Fingerprint: {fingerprint}")
            _logger.error(f"Context ID: {context_id}")
            return False
