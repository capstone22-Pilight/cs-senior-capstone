function buildquerydata() {
    query = {
        "hierarchy": $("input[name=hierarchy]:checked").val(),
        "time": {}
    };

    // Get the on time
    if ($("input[name=time_on][value=other]")[0].checked) {
        query.time.on = $("input[name=time_on][type=time]").val();
    } else {
        query.time.on = $("input[name=time_on]:checked").val();
    }

    // Get the off time
    if ($("input[name=time_off][value=other]")[0].checked) {
        query.time.off = $("input[name=time_off][type=time]").val();
    } else {
        query.time.off = $("input[name=time_off]:checked").val();
    }

    // Get the days of the week
    dow = [];
    $("input[name=dow]:checked").each(function() {
        dow.push(this.value);
    });
    if (dow.length > 0) {
        query.dow = dow;
    }

    // Get the days of the month
    dom_on = $("input[name=dom_on]").val();
    if (dom_on) {
        query.dom = [];
        query.dom.on = dom_on;
        dom_off = $("input[name=dom_off]").val();
        if (dom_off) {
            query.dom.off = dom_off;
        }
    }

    // Get the day of the year
    doy = {};
    $("input.doy").each(function() {
        if (this.value != "") {
            doy[this.name] = this.value;
        }
    });
    if (Object.keys(doy).length > 0) {
        query.doy = doy;
    }

    return query;
}

function buildquery() {
    data = buildquerydata();
    query = "time > " + data.time.on + " and time < " + data.time.off;

    dayqueries = [];
    if ("dow" in data) {
        dayqueries.push(Array.prototype.join.call(data.dow.map(function(e) { return "dow == " + e; }), " or "));
    }
    if ("dom" in data) {
        if ("off" in data.dom) {
            dayqueries.push("(dom >= " + data.dom.on + " and dom <= " + data.dom.off + ")")
        } else { // Only work for the "on" day
            dayqueries.push("dom == " + data.dom.on);
        }
    }
    if ("doy" in data) {
        dayqueries.push("(" + Array.prototype.join.call(Object.keys(data.doy).map(function(k) { return k + " == " + data.doy[k]; }), " and ") + ")");
    }
    if (dayqueries.length > 0) {
        query = "(" + query + ") and (" + dayqueries.join(" or ") + ")";
    }

    if (data.hierarchy == 'manual') {
        query = "manual";
    } else if (data.hierarchy == 'parent') {
        query = "parent";
    } else if (data.hierarchy == 'or') {
        query = "(" + query + ") or parent";
    } else if (data.hierarchy == 'and') {
        query = "(" + query + ") and parent";
    }
    // If the type is 'own', no changes are made to the query.

    return query;
}

$("input").on("change", function () {
    $("#query").val(buildquery());
});

$(window).on("load", function () {
    $("#query").val(buildquery());
});

$("input[name=advanced_override]").on("change", function () {
    if (this.checked) {
        $("#query").attr("disabled", false);
        $("#rightside").addClass("box-en");
        $("#leftside").find("input").attr("disabled", true);
        $("#leftside").removeClass("box-en");
    } else {
        $("#query").attr("disabled", true);
        $("#rightside").removeClass("box-en");
        $("#leftside").find("input").attr("disabled", false);
        $("#leftside").addClass("box-en");
    }
});

$("#create").on("click", function(event) {
    baserule = $(".baserule");
    newrule = baserule.clone();
    newrule.removeClass("baserule");
    newrule.find(".rulename").text($("input[name=name]")[0].value);
    newrule.appendTo(baserule.parent());
});

$(".deleterule").on("click", function() {
    event.preventDefault();
    this.parent().remove();
});

$(".editrule").on("click", function() {
    event.preventDefault();
});
