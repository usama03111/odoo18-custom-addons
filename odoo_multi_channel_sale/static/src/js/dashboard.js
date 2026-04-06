/** @odoo-module **/
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted } from "@odoo/owl";

export class MultichannelDashboard extends Component {

	setup() {
		this.actionService = useService("action");
		onWillStart(async () => {
			await loadJS("/web/static/lib/Chart/Chart.js");
			await this.fetch_data();
		});
		onMounted(() => {
			this.on_attach_callback();
		});

	}
	on_attach_callback() {
		this.render_line_graph()
		this.render_pie_graph()
	}
	reload_line_graph() {
		var self = this
		var selected_option = document.getElementById('line_obj_change').value
		var line_chart_label = document.getElementById('line_chart_label')
		switch (selected_option) {
			case 'order':
				line_chart_label.innerText = 'Sales Orders'
				break
			case 'product':
				line_chart_label.innerText = 'Products'
				break
			case 'category':
				line_chart_label.innerText = 'Categories'
				break
			case 'customer':
				line_chart_label.innerText = 'Customers'
				break
			default:
				line_chart_label.innerText = ''
		}

		self.fetch_data(
			selected_option,
			parseInt(document.getElementById('line_date_change').value),
		).then(function () {
			return self.render_line_graph()
		})
	}

	reload_pie_graph() {
		var selected_option = document.getElementById('pie_obj_change').value
		var pie_chart_label = document.getElementById('pie_chart_label')
		switch (selected_option) {
			case 'order':
				pie_chart_label.innerText = 'Sales Orders'
				break
			case 'product':
				pie_chart_label.innerText = 'Products'
				break
			case 'category':
				pie_chart_label.innerText = 'Categories'
				break
			case 'customer':
				pie_chart_label.innerText = 'Customers'
				break
			default:
				pie_chart_label.innerText = ''
		}
		this.render_pie_graph(selected_option)
	}

	fetch_data(obj = 'order', days = 7) {
		var self = this
		return rpc('/multichannel/fetch_dashboard_data', {
			obj: obj,
			days: days
		}).then(function (result) {
			self.line_data = result.line_data
			self.instance_data = result.instance_data
			self.connected_count = Object.values(result.instance_data).reduce(
				(n, i) => n + (i.connected === true), 0
			)
		})
	}

	render_line_graph() {
		const oldCanvas = document.getElementById('line_chart');
		const newCanvas = document.createElement('canvas');
		newCanvas.id = 'line_chart';
		oldCanvas.replaceWith(newCanvas);
		var self = this
		self.line_chart = new Chart('line_chart', {
			type: 'line',
			data: {
				labels: self.line_data.labels,
				datasets: self.line_data.data.map(i => ({
					borderColor: i.color,
					data: i.count,
					label: i.name,
					fill: false,
				})),
			},
			beginAtZero: false,
			options: {
				maintainAspectfirefoxRatio: false,
				legend: {
					display: false,
				},
				tooltip: {
					enabled: false,
				},
				scales: {
					x: {
						display: true,
					},
					y: {
						display: true,
						ticks: {
							precision: 0,
						},
					}
				},
			},
		})
	}

	render_pie_graph(obj = 'order') {
		const oldCanvas = document.getElementById('pie_chart');
		const newCanvas = document.createElement('canvas');
		newCanvas.id = 'pie_chart';
		oldCanvas.replaceWith(newCanvas);
		var self = this
		self.pie_chart = new Chart('pie_chart', {
			type: 'pie',
			data: {
				labels: Object.keys(self.instance_data),
				datasets: [{
					backgroundColor: Object.values(self.instance_data).map(i => i['color']),
					data: Object.values(self.instance_data).map(i => i[obj + '_count']),
				}],
			},
			options: {
				maintainAspectRatio: false,
				cutoutPercentage: 45,
				legend: {
					position: 'bottom',
					labels: {
						usePointStyle: true,
					},
				},
			},
		})
	}

	on_action(e) {
		e.preventDefault()
		var target = e.currentTarget
		var action = target.dataset.action
		var object = target.dataset.object
		var channel_id = target.dataset.channel

		switch (action) {
			case 'import':
				return this.actionService.doAction('odoo_multi_channel_sale.open_import_wizard_action')
			case 'export':
				return this.actionService.doAction('odoo_multi_channel_sale.open_export_wizard_action')
			case 'open':
				return this.actionService.doAction({
					name: 'Instance',
					type: 'ir.actions.act_window',
					res_model: 'multi.channel.sale',
					views: [[false, 'form']],
					target: 'current',
				})
		}

		if (object && channel_id) {
			var res_model
			switch (object) {
				case 'product':
					res_model = 'channel.template.mappings'
					break
				case 'order':
					res_model = 'channel.order.mappings'
					break
				case 'category':
					res_model = 'channel.category.mappings'
					break
				case 'customer':
					res_model = 'channel.partner.mappings'
					break
				default:
					pie_chart_label.text('')
			}
			if (res_model)
				return this.actionService.doAction({
					name: 'Mapping',
					type: 'ir.actions.act_window',
					res_model,
					domain: [['channel_id', '=', channel_id]],
					views: [[false, 'list'], [false, 'form']],
					target: 'main',
				})
		}

		if (channel_id)
			sessionStorage.setItem("channel_id", channel_id);
		return this.actionService.doAction({
			type: 'ir.actions.client',
			tag: 'dashboard_instance',
			params: { id: channel_id },
		})
	}
}
MultichannelDashboard.template = "multichannel_dashboard_template";

registry.category("actions").add("dashboard_multichannel", MultichannelDashboard);

export class InstanceDashboard extends Component {
	setup() {
		this.actionService = useService("action");
		this.id = sessionStorage.getItem("channel_id");
		onWillStart(async () => {
			await loadJS("/web/static/lib/Chart/Chart.js");
			await this.fetch_data();
		});
		onMounted(() => {
			this.on_attach_callback();
		});

	}
	on_attach_callback() {
		for (let obj of ['product', 'order', 'category', 'customer'])
			this.render_line_graph(obj)
		// $('[data-toggle="tooltip"]').tooltip()
	}

	change_graph(e) {
		var target = e.currentTarget
		Array.from(target.parentNode.children).forEach(c => c.classList.remove('active'))
		target.classList.add('active')
		this['render_' + target.dataset.mode + '_graph'](target.dataset.object)
	}

	fetch_data() {
		var self = this
		return rpc('/multichannel/fetch_dashboard_data/' + this.id, { period: 'year' }
		).then(function (result) {
			self.labels = result.labels
			self.data = result.data
			self.counts = result.counts
		})
	}

	render_line_graph(obj) {
		const oldCanvas = document.getElementById(obj + '_chart');
		const newCanvas = document.createElement('canvas');
		newCanvas.id = obj + '_chart';
		oldCanvas.replaceWith(newCanvas);
		var self = this
		var data = self.data[obj + '_count']
		if (data.length)
			self.chart = new Chart(obj + '_chart', {
				type: 'line',
				data: {
					labels: self.labels,
					datasets: [{
						data,
						borderColor: self.data.color,
						backgroundColor: self.data.color + '66',
					}],
				},
				options: {
					maintainAspectRatio: false,
					legend: {
						display: false,
					},
					tooltip: {
						enabled: false,
					},
					scales: {
						x: {
							display: true,
						},
						y: {
							display: true,
							ticks: {
								precision: 0,
							},
						},
					},
				},
			})
	}

	render_pie_graph(obj) {
		const oldCanvas = document.getElementById(obj + '_chart');
		const newCanvas = document.createElement('canvas');
		newCanvas.id = obj + '_chart';
		oldCanvas.replaceWith(newCanvas);
		var self = this
		var labels = self.counts[obj].types
		if (labels) {
			var backgroundColor = labels.map(x => self.data.color + '66')
			var borderColor = labels.map(x => self.data.color)
			self.pie_chart = new Chart(obj + '_chart', {
				type: 'pie',
				data: {
					labels,
					datasets: [{
						backgroundColor,
						borderColor,
						hoverBackgroundColor: borderColor,
						data: self.counts[obj].counts,
					}],
				},
				options: {
					maintainAspectRatio: false,
					legend: {
						display: false,
					},
				},
			})
		}
	}

	on_action(e) {
		e.preventDefault()
		var self = this
		var target = e.currentTarget
		var action = target.dataset.action
		var instance = target.dataset.instance
		var obj = target.dataset.obj
		var type = target.dataset.type
		var feed = target.dataset.feed
		var state = target.dataset.state
		var report = target.dataset.report
		var count = target.dataset.count
		var reload = target.dataset.reload
		if (reload)
			target.classList.add('fa-spin')

		if (action && instance)
			switch (action) {
				case 'import':
					return this.actionService.doAction('odoo_multi_channel_sale.open_import_wizard_action', {
						additionalContext: {
							default_channel_id: instance,
						},
					})
				case 'export':
					return this.actionService.doAction('odoo_multi_channel_sale.open_export_wizard_action', {
						additionalContext: {
							default_channel_id: instance,
						},
					})
				case 'open':
					return this.actionService.doAction({
						name: 'Instance',
						type: 'ir.actions.act_window',
						res_model: 'multi.channel.sale',
						res_id: instance,
						views: [[false, 'form']],
						target: 'main'
					})
				case 'evaluate':
					return this.actionService.doAction('odoo_multi_channel_sale.action_feed_sync', {
						additionalContext: {
							default_channel_id: instance,
						},
					})
			}

		if (obj && report)
			return this.actionService.doAction({
				name: 'Report',
				type: 'ir.actions.act_window',
				res_model: 'channel.synchronization',
				domain: [
					['channel_id', '=', instance],
					['action_on', '=', obj],
					['status', '=', report],
				],
				views: [
					[false, 'list'],
					[false, 'form'],
				],
				target: 'main',
			})

		if (obj && reload)
			return rpc({
				model: 'channel.order.mappings',
				method: 'update_order_mapping_status',
				args: [instance],
			}).then(
				location.reload()
			)

		if (obj) {
			var name, res_model, domain, mapping_model, odoo_mapping_field
			switch (obj) {
				case 'product':
					name = 'Product'
					res_model = 'product.template'
					mapping_model = 'channel.template.mappings'
					odoo_mapping_field = 'odoo_template_id'
					break
				case 'order':
					name = 'Order'
					res_model = 'sale.order'
					mapping_model = 'channel.order.mappings'
					odoo_mapping_field = 'odoo_order_id'
					break
				case 'category':
					name = 'Category'
					res_model = 'product.category'
					mapping_model = 'channel.category.mappings'
					odoo_mapping_field = 'odoo_category_id'
					break
				case 'customer':
					name = 'Customer'
					res_model = 'res.partner'
					mapping_model = 'channel.partner.mappings'
					odoo_mapping_field = 'odoo_partner_id'
					break
			}
			if (name)
				if (count) {
					switch (count) {
						case 'mapped':
							domain = [['channel_id', '=', instance]]
							break
						case 'to_update':
							domain = [['channel_id', '=', instance], ['need_sync', '=', 'yes']]
							break
						case 'to_deliver':
							domain = [['channel_id', '=', instance], ['is_delivered', '=', false]]
							break
						case 'to_invoice':
							domain = [['channel_id', '=', instance], ['is_invoiced', '=', false]]
							break
					}
					if (domain)
						return self.actionService.doAction({
							name: 'Mapping',
							type: 'ir.actions.act_window',
							res_model: mapping_model,
							domain,
							views: [
								[false, 'list'],
								[false, 'form'],
							],
							target: 'main',
						})
				}
			return rpc({
				model: 'multi.channel.sale',
				method: 'open_record_view',
				args: [instance],
				context: {
					mapping_model,
					odoo_mapping_field,
				},
			}).then(function (result) {
				var domain = result.domain
				if (count && count === 'to_export')
					domain[0][1] = 'not in'
				if (type) {
					if (obj === 'product') {
						if (type === 'multi_variant')
							domain.push(['attribute_line_ids', '!=', false])
						else
							if (type === 'single_variant')
								domain.push(['attribute_line_ids', '=', false])
					}
					else
						if (obj === 'order') {
							domain.push(['state', '=', type])
						}
						else
							if (obj === 'customer') {
								if (type === 'other')
									domain.push(['type', 'not in', ['invoice', 'delivery']])
								else
									domain.push(['type', '=', type])
							}
				}
				return this.actionService.doAction({
					name,
					type: 'ir.actions.act_window',
					res_model,
					domain,
					views: [
						[false, 'list'],
						[false, 'form'],
					],
					target: 'main',
				})
			})
		}

		if (feed && state)
			return self.actionService.doAction({
				name: 'Feed',
				type: 'ir.actions.act_window',
				res_model: feed,
				domain: [
					['channel_id', '=', instance],
					['state', '=', state],
				],
				views: [
					[false, 'list'],
					[false, 'form'],
				],
				target: 'main',
			})
	}
}
InstanceDashboard.template = "instance_dashboard_template";

registry.category("actions").add("dashboard_instance", InstanceDashboard);
