function buildquery() {
    hierarchy = $("input[name=hierarchy]:checked").val();
    hierquery = ""
    query = "((" + buildquery_time() + ") AND (" + buildquery_dow() + "))";
    if (hierarchy == 'group') {
        hierquery = "PARENT";
    } else if (hierarchy == 'own') {
        hierquery = query;
    } else if (hierarchy == 'or') {
        hierquery = query + " OR PARENT";
    } else if (hierarchy == 'and') {
        hierquery = query + " AND PARENT";
    } else {
        hierquery = "MANUAL";
    }
    return hierquery;
}

function buildquery_dow() {
    var elements = [];
    $("input[name=day]:checked").each(function()
    {
        elements.push("day == '" + $(this).val() + "'");
    });
    return elements.join(" OR ");
}

function buildquery_time() {
    time_on = $("input[name=time_on]:checked");
    if (time_on.val() == "other") {
        time_on = $("input[type=time][name=time_on]").val()
    } else {
        time_on = time_on.val()
    }

    time_off = $("input[name=time_off]:checked");
    if (time_off.val() == "other") {
        time_off = $("input[type=time][name=time_off]").val()
    } else {
        time_off = time_off.val()
    }

    return "time > " + time_on + " AND time < " + time_off;
}


$("input").on("change", function () {
    $("#query").val(buildquery())
});

$(window).on("load", function () {
    $("#query").val(buildquery())
});
