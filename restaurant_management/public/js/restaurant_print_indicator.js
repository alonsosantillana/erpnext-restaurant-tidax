(() => {
    frappe.provide("frappe.restaurant_print_indicator");

    const indicator = frappe.restaurant_print_indicator;
    const refresh_interval_ms = 10000;

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
        let icon = $("#restaurant-navbar-printer");
        if (icon.length) return icon;

        icon = $(
            '<a id="restaurant-navbar-printer" class="navbar-center ellipsis" '
            + 'href="/app/restaurant-print-console" target="_blank" '
            + 'style="color:#d97706;margin-right:8px;cursor:pointer" '
            + 'aria-label="Estación de impresión">'
            + '<i class="fa fa-print"></i></a>'
        );
        icon.on("click", () => {
            localStorage.removeItem("_page:restaurant-print-console");
        });
        $(".navbar-brand.navbar-home").before(icon);
        return icon;
    };

    const render = (station) => {
        const icon = ensure_icon();
        const state = state_details(station);
        const title = `${station.station_name} · ${state.label}`;
        icon.css("color", state.color).attr("title", title).attr("aria-label", title);

        // An assigned restaurant station supersedes the global legacy indicator.
        $("#navbar-printer").hide();
    };

    const refresh = async () => {
        try {
            const response = await frappe.call({
                method: "restaurant_management.printing.get_station_bootstrap",
                type: "GET",
                silent: true,
            });
            const stations = response.message?.stations || [];
            if (!stations.length) {
                $("#restaurant-navbar-printer").remove();
                return;
            }
            render(stations[0]);
        } catch (error) {
            const icon = $("#restaurant-navbar-printer");
            if (icon.length) {
                icon.css("color", "#dc2626").attr("title", __("No se pudo consultar la estación de impresión"));
            }
        }
    };

    const initialize = () => {
        if (indicator.initialized) return;
        indicator.initialized = true;
        refresh();
        indicator.timer = window.setInterval(refresh, refresh_interval_ms);
        frappe.realtime.on("restaurant_print_job", refresh);
        frappe.realtime.on("restaurant_print_station", refresh);
    };

    $(document).on("app_ready", initialize);
})();
