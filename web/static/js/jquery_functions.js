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
      data = {
         lid: $(this).closest('li').attr('lid'),
         state: state
      };
      // Dont change the state of the switch until we have confirmation
      $(this).bootstrapSwitch('state', !state, true);
   
      $.ajax({
         url: "/enlighten",
         global: false,
         type: "POST",
         data:  data,
         cache: "false",
         success: function(response) {
            if(response == "OK") {
               light_switch = $("li[lid='" + data.lid + "'] input[name='light-switch']:first");
               light_switch.bootstrapSwitch('state', state, true);
            }
            else {
               light_name = $("li[lid='" + data.lid + "'] span.edit:first").text();
               alert("Unable to change light '" + light_name + "': " + response);
            }
         }
      });
   });
},true);

function enlighten_group(gid, action) {
   group = $("li[gid='" + gid + "']").first();
   lights = $(group).find("input[name='light-switch']");

   for (var i = 0; i < lights.length; i++) {
      $(lights[i]).bootstrapSwitch('state', action);
   }
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

