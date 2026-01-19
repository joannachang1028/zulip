import $ from "jquery";
import * as z from "zod/mini";

import render_message_recap from "../templates/message_recap.hbs";

import * as channel from "./channel.ts";
import * as dialog_widget from "./dialog_widget.ts";
import {$t} from "./i18n.ts";
import * as rendered_markdown from "./rendered_markdown.ts";

export function show_message_recap(): void {
    const modal_id = "message-recap-modal";

    dialog_widget.launch({
        text_heading: $t({defaultMessage: "Message Recap"}),
        html_body: `<div class="loading-indicator"></div>`,
        close_on_submit: true,
        id: modal_id,
        footer_minor_text: $t({defaultMessage: "AI summaries may have errors."}),
        html_submit_button: $t({defaultMessage: "Close"}),
        on_click() {
            // Just close the modal
        },
        single_footer_button: true,
        post_render() {
            const close_on_success = false;
            dialog_widget.submit_api_request(
                channel.get,
                "/json/messages/recap",
                {},
                {
                    success_continuation(response_data) {
                        const data = z.object({summary: z.string()}).parse(response_data);
                        const summary_html = render_message_recap({
                            summary_html: data.summary,
                        });
                        $(`#${CSS.escape(modal_id)} .modal__content`).addClass("rendered_markdown");
                        $(`#${CSS.escape(modal_id)} .modal__content`).html(summary_html);
                        rendered_markdown.update_elements($(`#${CSS.escape(modal_id)} .modal__content`));
                    },
                    failure_msg_html: $t({defaultMessage: "Failed to generate recap"}),
                },
                close_on_success,
            );
        },
    });
}
