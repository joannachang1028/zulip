import $ from "jquery";

import render_navbar_help_menu from "../templates/popovers/navbar/navbar_help_menu_popover.hbs";

import * as message_recap from "./message_recap.ts";
import {page_params} from "./page_params.ts";
import * as popover_menus from "./popover_menus.ts";
import {current_user} from "./state_data.ts";
import {parse_html} from "./ui_util.ts";

export function initialize(): void {
    popover_menus.register_popover_menu("#help-menu", {
        theme: "popover-menu",
        placement: "bottom",
        offset: [-50, 0],
        // The strategy: "fixed"; and eventlisteners modifier option
        // ensure that the personal menu does not modify its position
        // or disappear when user zooms the page.
        popperOptions: {
            strategy: "fixed",
            modifiers: [
                {
                    name: "eventListeners",
                    options: {
                        scroll: false,
                    },
                },
            ],
        },
        onMount(instance) {
            popover_menus.popover_instances.help_menu = instance;
            const $popper = $(instance.popper);
            $popper.one("click", ".sidebar-popover-message-recap", () => {
                message_recap.show_message_recap();
                popover_menus.hide_current_popover_if_visible(instance);
            });
        },
        onShow(instance) {
            instance.setContent(
                parse_html(
                    render_navbar_help_menu({
                        corporate_enabled: page_params.corporate_enabled,
                        is_owner: current_user.is_owner,
                        is_admin: current_user.is_admin,
                    }),
                ),
            );
            $("#help-menu").addClass("active-navbar-menu");
        },
        onHidden(instance) {
            instance.destroy();
            popover_menus.popover_instances.help_menu = null;
            $("#help-menu").removeClass("active-navbar-menu");
        },
    });
}

export function toggle(): void {
    // NOTE: Since to open help menu, you need to click on help navbar icon (which calls
    // tippyjs.hideAll()), or go via gear menu if using hotkeys, we don't need to
    // call tippyjs.hideAll() for it.
    $("#help-menu").trigger("click");
}
