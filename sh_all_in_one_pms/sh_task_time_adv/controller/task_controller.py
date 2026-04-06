# -*- coding: utf-8 -*-
import functools

from odoo import _ , fields
from odoo.http import request
from odoo.http import Controller, route, request


class ImportModule(Controller):

    # for running task information
    @route('/user/current/task/information',
        type='json', auth='user', methods=['POST'])
    def get_task_details(self, **kwargs):
        user = request.env.user
        if user.task_id and user.start_time:
            start_timestamp = fields.Datetime.to_datetime(user.start_time).timestamp() * 1000
            return {"start_timestamp": start_timestamp}
        return {"start_timestamp": None}

    # for end task information
    @route('/end/task/information', type='json', auth='user', methods=['POST'])
    def get_end_task_details(self, user_id=None, **kwargs):
        user = request.env.user
        if user_id:
            user = request.env['res.users'].browse(user_id)
        if user.task_id:
            return [user.task_id.id, user.task_id.start_time]
        else:
            return False