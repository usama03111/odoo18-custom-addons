/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Composer } from "@mail/core/common/composer";

const superPostMessage = Composer.prototype.postMessage;
const superSendMessage = Composer.prototype.sendMessage;

// Session-scoped cache to avoid extra RPC calls per channel id
const canPostCacheByChannelId = new Map();

function showPermissionNotification(env) {
	const notification = env?.services?.notification;
	if (notification) {
		notification.add(
			_t("You don't have permission to send messages in this channel."),
			{
				title: _t("Permission Denied"),
				type: "danger",
			}
		);
	}
}

function getCurrentChannelId(composer) {
	const thread = composer?.thread || composer?.props?.thread;
	return thread?.id || thread?.channel?.id || null;
}

async function ensureCanPost(env, composer) {
	try {
		const channelId = getCurrentChannelId(composer);
		if (!channelId) {
			return true;
		}
		if (canPostCacheByChannelId.has(channelId)) {
			const cached = canPostCacheByChannelId.get(channelId);
			if (!cached) {
				showPermissionNotification(env);
			}
			return cached;
		}
		const result = await env.services.orm.call(
			"discuss.channel",
			"can_current_user_post",
			[[channelId]]
		);
		canPostCacheByChannelId.set(channelId, Boolean(result));
		if (!result) {
			showPermissionNotification(env);
			return false;
		}
		return true;
	} catch (e) {
		// On any error, do not block, let normal flow happen
		return true;
	}
}

// Patch Composer methods (some builds use postMessage, others sendMessage)
patch(
	Composer.prototype,
	{
		async postMessage(...args) {
			if (!(await ensureCanPost(this.env, this))) {
				return false;
			}
			try {
				return await superPostMessage.call(this, ...args);
			} catch (error) {
				showPermissionNotification(this.env);
				return false;
			}
		},
	},
	{ name: "oh_discuss_general_restrict.composer_postMessage_notification" }
);

if (typeof superSendMessage === "function") {
	patch(
		Composer.prototype,
		{
			async sendMessage(...args) {
				if (!(await ensureCanPost(this.env, this))) {
					return false;
				}
				try {
					return await superSendMessage.call(this, ...args);
				} catch (error) {
					showPermissionNotification(this.env);
					return false;
				}
			},
		},
		{ name: "oh_discuss_general_restrict.composer_sendMessage_notification" }
	);
}

// Patch RPC service to catch backend ValidationError on message_post (guarded by try/catch)
try {
	const rpcService = registry.category("services").get("rpc");
	if (rpcService && typeof rpcService.rpc === "function") {
		const originalRpc = rpcService.rpc;
		patch(
			rpcService,
			{
				async rpc(route, params, options) {
					try {
						return await originalRpc.call(this, route, params, options);
					} catch (error) {
						const isMessagePost =
							params && params.model === "discuss.channel" && params.method === "message_post";
						if (isMessagePost && this?.env) {
							showPermissionNotification(this.env);
						}
						throw error;
					}
				},
			},
			{ name: "oh_discuss_general_restrict.rpc_message_post_notification" }
		);
	}
} catch (e) {
	// Silently ignore if the rpc service is not available in this build
}
