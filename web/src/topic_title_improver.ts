import $ from "jquery";
import * as z from "zod/mini";

import * as channel from "./channel.ts";
import * as confirm_dialog from "./confirm_dialog.ts";
import * as dialog_widget from "./dialog_widget.ts";
import {$t, $t_html} from "./i18n.ts";
import * as message_edit from "./message_edit.ts";

const suggestion_schema = z.object({
    has_drifted: z.boolean(),
    suggested_title: z.nullable(z.string()),
    reason: z.string(),
});

export function show_topic_title_suggestion(stream_id: number, topic_name: string): void {
    const modal_id = "topic-title-improver-modal";

    dialog_widget.launch({
        text_heading: $t({defaultMessage: "Improve Topic Title"}),
        html_body: `<div class="loading-indicator"><p>${$t({defaultMessage: "Analyzing topic..."})}</p></div>`,
        close_on_submit: true,
        id: modal_id,
        footer_minor_text: $t({defaultMessage: "AI suggestions may have errors."}),
        html_submit_button: $t({defaultMessage: "Close"}),
        on_click() {
            // Just close
        },
        single_footer_button: true,
        post_render() {
            const close_on_success = false;
            dialog_widget.submit_api_request(
                channel.get,
                "/json/topic/suggest_title",
                {stream_id, topic_name},
                {
                    success_continuation(response_data) {
                        const data = suggestion_schema.parse(response_data);
                        let html_content: string;

                        if (data.has_drifted && data.suggested_title) {
                            html_content = `
                                <div class="topic-title-suggestion">
                                    <p><strong>${$t({defaultMessage: "Current title:"})}</strong> ${topic_name}</p>
                                    <p><strong>${$t({defaultMessage: "Suggested title:"})}</strong> ${data.suggested_title}</p>
                                    <p><em>${data.reason}</em></p>
                                    <button class="button rounded sea-green apply-suggested-title" data-suggested-title="${data.suggested_title}">
                                        ${$t({defaultMessage: "Apply suggested title"})}
                                    </button>
                                </div>
                            `;
                        } else {
                            html_content = `
                                <div class="topic-title-suggestion">
                                    <p>✓ ${$t({defaultMessage: "The current topic title is appropriate."})}</p>
                                    <p><em>${data.reason}</em></p>
                                </div>
                            `;
                        }

                        $(`#${CSS.escape(modal_id)} .modal__content`).html(html_content);

                        // Handle apply button click
                        $(`#${CSS.escape(modal_id)} .apply-suggested-title`).on("click", function () {
                            const suggested_title = $(this).attr("data-suggested-title")!;
                            dialog_widget.close();
                            apply_suggested_title(stream_id, topic_name, suggested_title);
                        });
                    },
                    failure_msg_html: $t({defaultMessage: "Failed to analyze topic"}),
                },
                close_on_success,
            );
        },
    });
}

function apply_suggested_title(
    stream_id: number,
    old_topic_name: string,
    new_topic_name: string,
): void {
    // Use Zulip's existing topic rename functionality
    confirm_dialog.launch({
        html_heading: $t_html({defaultMessage: "Rename topic"}),
        html_body: `<p>${$t({defaultMessage: "Rename topic from '{old_topic}' to '{new_topic}'?"}, {old_topic: old_topic_name, new_topic: new_topic_name})}</p>`,
        on_click() {
            message_edit.with_first_message_id(stream_id, old_topic_name, (message_id) => {
                if (message_id !== undefined) {
                    void channel.patch({
                        url: `/json/messages/${message_id}`,
                        data: {
                            topic: new_topic_name,
                            propagate_mode: "change_all",
                        },
                    });
                }
            });
        },
    });
}
