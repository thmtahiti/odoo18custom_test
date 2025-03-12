/** @odoo-module **/
import { registry } from '@web/core/registry';
import { ListRenderer } from '@web/views/list/list_renderer';

export class PayslipListRenderer extends ListRenderer {}

registry.category('views').add('payslip_list', {
    type: 'list',
    Component: PayslipListRenderer,
});
