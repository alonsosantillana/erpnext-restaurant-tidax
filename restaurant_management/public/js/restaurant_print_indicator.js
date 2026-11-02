(() => {
    frappe.provide("frappe.restaurant_print_indicator");

    const indicator = frappe.restaurant_print_indicator;
    const refresh_interval_ms = 10000;
    let icon;
    let current_station;
    let refresh_failed = false;

    const mount_icon = (node) => {
        const legacy_anchor = $(".navbar-brand.navbar-home:visible").first();
        if (legacy_anchor.length) {
            legacy_anchor.before(node);
            return true;
        }
        const header = $(frappe.container?.page)
            .find(".page-head:visible .standard-items-section").first();
        const host = header.length ? header : $(".body-sidebar .standard-items-band:visible").first();
        if (!host.length) return false;
        host.prepend(node); // One host only: moving, not cloning across cached pages.
        return true;
    };

    const state_details = (station) => {
        if (!station.active) {
            return {color: "#64748b", label: __("Estación de impresión inactiva")};
        }
        if (station.bridge_state === "open") {
            return {color: "#16a34a", label: __("Ticketera conectada")};
        }
        if (["idle", "connecting"].includes(station.bridge_state)) {
            return {color: "#d97706", label: __("Conectando con la ticketera")};
        }
        return {color: "#dc2626", label: __("WebApp Hardware Bridge desconectado")};
    };

    const ensure_icon = () => {
        if (!icon) {
            icon = $(
                '<a id="restaurant-navbar-printer" class="btn-reset icon-btn" '
                + 'href="/app/restaurant-print-console" target="_blank" '
                + 'rel="noopener noreferrer" '
                + 'style="color:#d97706;margin-right:8px;cursor:pointer;display:inline-flex;align-items:center" '
                + 'aria-label="Estación de impresión">'
                + frappe.utils.icon("printer", "sm") + '</a>'
            );
            icon.find("svg").css({
                "--icon-stroke": "currentColor", "--icon-fill": "none",
                stroke: "currentColor", fill: "none",
            });
            icon.on("click", () => {
                localStorage.removeItem("_page:restaurant-print-console");
            });
        }
        mount_icon(icon);
        return icon;
    };

    const render = (station) => {
        const icon = ensure_icon();
        const state = refresh_failed
            ? {color: "#dc2626", label: __("No se pudo consultar la estación de impresión")}
            : state_details(station);
        const title = `${station.station_name} · ${state.label}`;
        icon.css("color", state.color).attr("title", title).attr("aria-label", title);

        // An assigned restaurant station supersedes the global legacy indicator.
        if (icon[0]?.isConnected) $("#navbar-printer").hide();
    };

    const refresh = async () => {
        try {
            const response = await frappe.call({
                method: "restaurant_management.printing.get_station_bootstrap",
                type: "GET",
                silent: true,
            });
            const stations = response.message?.stations || [];
            refresh_failed = false;
            current_station = stations[0];
            if (!stations.length) {
                if (icon) icon.remove();
                icon = null;
                // Never initialize a receiver here: restore only an existing,
                // already authorized Silent Print control.
                $("#navbar-printer").show();
                return;
            }
            render(stations[0]);
        } catch (error) {
            refresh_failed = true;
            if (current_station) render(current_station);
        }
    };

    const initialize = () => {
        if (indicator.initialized) return;
        indicator.initialized = true;
        refresh();
        indicator.timer = window.setInterval(refresh, refresh_interval_ms);
        frappe.realtime.on("restaurant_print_job", refresh);
        frappe.realtime.on("restaurant_print_station", refresh);
        $(document).on("page-change", () => {
            if (current_station) render(current_station);
        });
    };

    $(document).on("app_ready", initialize);
})();
