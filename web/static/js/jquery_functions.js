document.addEventListener("DOMContentLoaded", function() {
   $("#add_devices").click(function(){
      $('#response').html('<img id="loading" src="/static/images/search.gif" />').show();
      $.ajax({
         url: "/devices/search",
         global: false,
         type: "POST",
         cache: false,
         beforeSend: function(){
            $('#response').remove('#add_devices');
            $('#response').html('<img id="loading" src="/static/images/search.gif" />');
         },
         success: function(response){
            console.log(response)
               if (response == "NODHCP"){
                  $('img[src*="search.gif"]').remove();
                  $('#response').html('<div class="alert alert-danger"><strong>Error!</strong> No devices connected!</div>');
               }else if (response == "0"){
                  $('img[src*="search.gif"]').remove();
                  $('#response').html('<div class="alert alert-warning"><strong>Done!</strong> Scan complete. No new devices added</div>');
               }else{
                  $('img[src*="search.gif"]').remove();
                  $('#response').html('<div class="alert alert-success"><strong>Done!</strong> Scan complete. New devices added</div>');

               }
         }
      });
   });

   $('input[name="light-switch"]').on('switchChange.bootstrapSwitch', function(event, state) {
      // Dont change the state of the switch until we have confirmation
      $(this).bootstrapSwitch('state', !state, true);
      enlighten_light($(this), state);
   });
},true);

function enlighten_light(light, action) {
   var data = {
      lid: light.closest('li').attr('lid'),
      action: action
   };

   $.ajax({
      url: "/enlighten_light",
      global: false,
      type: "POST",
      data:  data,
      cache: "false",
      success: function(response) {
         console.log(response);
         if(response == "OK") {
            console.log("successful update")
            var light_switch = $("li[lid='" + data.lid + "'] input[name='light-switch']:first");
            light_switch.bootstrapSwitch('state', action, true);
         }
         else {
            console.log("error")
            var light_name = $("li[lid='" + data.lid + "'] span.edit:first").text();
            alert("Unable to change light '" + light_name + "': " + response);
         }
      }
   });
}

function enlighten_group(gid, action) {
   var group = $("li[gid='" + gid + "']").first();
   var lights = $(group).find("input[name='light-switch']");

   for (var i = 0; i < lights.length; i++) {
      if($(lights[i]).bootstrapSwitch('state') != action) {
         enlighten_light($(lights[i]), action);
      }
   }

   var data = {
      gid: gid,
      action: action
   };

   $.ajax({
      url: "/enlighten_group",
      global: false,
      type: "POST",
      data:  data,
      cache: "false",
      success: function(response) {
         console.log(response)
      }
   });
}

function delete_group(id) {
   group_name = $("[gid='" + id + "'] span.edit:first").text();
   if(!window.confirm("Are you sure you want to delete group '" + group_name + "'?"))
      return;
   $.ajax({
      url: "/delete_group",
      global: false,
      type: "POST",
      cache: false,
      data: 'id=' + id,
      success: function(response){
         console.log(response);
         $("[gid='" + id + "']").before($("[gid='" + id + "'] ol:first").children());
         $("[gid='" + id + "']").remove()
      }
   });
}

function add_group() {
   $.ajax({
      url: "/new_group",
      global: false,
      type: "POST",
      cache: false,
      success: function(response){
         console.log(response);
         $(".vertical ol").first().append(response);
         $(".edit").editable();
      }
   });
}

