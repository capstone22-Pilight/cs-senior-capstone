function buildquerydata() {
    querydata = {
        "hierarchy": $("input[name=hierarchy]:checked").val(),
        "custom_query": "",
        "time": {
            "on": {
                "time": "",
                "early": "",
                "late": ""
            },
            "off": {
                "time": "",
                "early": "",
                "late": ""
            }
        },
        "dow": [],
        "range": {
            "on": {
                "year": "",
                "month": "",
                "day": ""
            },
            "off": {
                "year": "",
                "month": "",
                "day": ""
            }
        }
    };

    // Get the custom query if one is set
    if ($("input[name=custom_query_override]")[0].checked) {
        querydata.custom_query = $("#query").val();
    }

    // Get the on time
    if ($("input[name=time_on][value=other]")[0].checked) {
        querydata.time.on.time = $("input[name=time_on][type=time]").val();
    } else {
        querydata.time.on.time = $("input[name=time_on]:checked").val();
    }

    // Get the off time
    if ($("input[name=time_off][value=other]")[0].checked) {
        querydata.time.off.time = $("input[name=time_off][type=time]").val();
    } else {
        querydata.time.off.time = $("input[name=time_off]:checked").val();
    }

    // Get the toggle early/late times
    querydata.time.on.early = $("input[name=time_on_early]").val()
    querydata.time.on.late = $("input[name=time_on_late]").val()
    querydata.time.off.early = $("input[name=time_off_early]").val()
    querydata.time.off.late = $("input[name=time_off_late]").val()

    // Get the days of the week
    $("input[name=dow]:checked").each(function() {
        querydata.dow.push(this.value);
    });

    // Get the years/months/days range
    querydata.range.on.year = $("input.range[name=year_on]").val()
    querydata.range.on.month = $("input.range[name=month_on]").val()
    querydata.range.on.day = $("input.range[name=day_on]").val()
    querydata.range.off.year = $("input.range[name=year_off]").val()
    querydata.range.off.month = $("input.range[name=month_off]").val()
    querydata.range.off.day = $("input.range[name=day_off]").val()

    return querydata;
}

function readquerydata(data) {
    console.log(data);
    // Set the on time
    if(isNaN(data.time.on.time.replace(':', ''))){
        $("input[name=time_on][value=" + data.time.on + "]").attr("checked", true);
    }
    else {
        $("input[name='time_on'][value=other]").attr("checked", true);
        $("input[name='time_on'][type=time]").val(data.time.on);
    }

    // Set the off time
    if(isNaN(data.time.off.time.replace(':', ''))){
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

    for (var key in data.range){
        $(".range[name=" + key + "]").val(data.range[key])
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
    if ("range" in data) {
        dayqueries.push("(" + Array.prototype.join.call(Object.keys(data.range).map(function(k) { return k + " == " + data.range[k]; }), " and ") + ")");
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

function sendupdate(querydata) {
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
}

// When the form is edited...
$("input").on("change", function () {
    // Rebuild the query data structure
    querydata = buildquerydata();
    // Update the advanced query box with the new query
    $("#query").val(buildquery(querydata));
    // Send the updated query info to the server
    sendupdate(querydata);
});
$("#query").on("change", function () {
    // Rebuild the query data structure
    querydata = buildquerydata();
    // We don't update the advanced query box since it has custom data now
    // Send the updated query info to the server
    sendupdate(querydata);
});

$(window).on("load", function () {
    // Rebuild the query data structure
    querydata = buildquerydata();
    // Update the advanced query box with the new query
    $("#query").val(buildquery(querydata));
});

$("input[name=custom_query_override]").on("change", function () {
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
