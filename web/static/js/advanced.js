function buildquerydata() {
    querydata = {
        "hierarchy": $("input[name=hierarchy]:checked").val(),
        "time": {}
    };

    // Get the on time
    if ($("input[name=time_on][value=other]")[0].checked) {
        querydata.time.on = $("input[name=time_on][type=time]").val();
    } else {
        querydata.time.on = $("input[name=time_on]:checked").val();
    }

    // Get the off time
    if ($("input[name=time_off][value=other]")[0].checked) {
        querydata.time.off = $("input[name=time_off][type=time]").val();
    } else {
        querydata.time.off = $("input[name=time_off]:checked").val();
    }

    // Get the days of the week
    dow = [];
    $("input[name=dow]:checked").each(function() {
        dow.push(this.value);
    });
    if (dow.length > 0) {
        querydata.dow = dow;
    }

    // Get the days of the month
    dom_on = $("input[name=dom_on]").val();
    if (dom_on) {
        querydata.dom = [];
        querydata.dom.on = dom_on;
        dom_off = $("input[name=dom_off]").val();
        if (dom_off) {
            querydata.dom.off = dom_off;
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
        querydata.doy = doy;
    }

    return querydata;
}

function readquerydata(data) {
    console.log(data);
    // Set the on time
    if(isNaN(data.time.on.replace(':', ''))){
        $("input[name=time_on][value=" + data.time.on + "]").attr("checked", true);
    }
    else {
        $("input[name='time_on'][value=other]").attr("checked", true);
        $("input[name='time_on'][type=time]").val(data.time.on);
    }

    // Set the off time
    if(isNaN(data.time.off.replace(':', ''))){
        $("input[name=time_off][value=" + data.time.off + "]").attr("checked", true);
    }
    else {
        $("input[name='time_off'][value=other]").attr("checked", true);
        $("input[name='time_off'][type=time]").val(data.time.off);
    }

    // Set the days of the week
    for (var i in data.dow){
        $("input[name=dow][value=" + data.dow[i] + "]").attr("checked", true);
    }

    for (var key in data.doy){
        $(".doy[name=" + key + "]").val(data.doy[key])
    }

    $("input[name=hierarchy][value=" + data.hierarchy + "]").attr("checked", true);
}

function buildquery(data) {
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

// When the form is edited...
$("input").on("change", function () {
    // Rebuild the query data structure
    querydata = buildquerydata();
    // Update the advanced query box with the new query
    $("#query").val(buildquery(querydata));
    // Send the updated query info to the server
    title = $("#title");
    postdata = {
        "querydata": querydata,
        "lid": title.attr("lid"),
        "gid": title.attr("gid")
    }
    $.ajax({
            url: "/advanced_update",
            global: false,
            type: "POST",
            cache: false,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            data: JSON.stringify(postdata),
            success: function(response){
                console.log(response);
            }
    });
});

$(window).on("load", function () {
    // Rebuild the query data structure
    querydata = buildquerydata();
    // Update the advanced query box with the new query
    $("#query").val(buildquery(querydata));
});

$("input[name=advanced_override]").on("change", function () {
    if (this.checked) {
        $("#query").attr("disabled", false);
        $("#custom_query").addClass("box-en");
        $("#basic_settings,#advanced_settings").find("input").attr("disabled", true);
        $("#basic_settings,#advanced_settings").removeClass("box-en");
    } else {
        $("#query").attr("disabled", true);
        $("#custom_query").removeClass("box-en");
        $("#basic_settings,#advanced_settings").find("input").attr("disabled", false);
        $("#basic_settings,#advanced_settings").addClass("box-en");
    }
});
