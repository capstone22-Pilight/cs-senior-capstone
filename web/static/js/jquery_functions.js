document.addEventListener("DOMContentLoaded", function() {
   $("#add_devices").click(function(){
      $('#response').html('<img id="loading" src="/static/css/search.gif" />').show();
      $.ajax({
         url: "/devices/search",
         global: false,
         type: "POST",
         cache: false,
         beforeSend: function(){
            $('#response').remove('#add_devices');
            $('#response').html('<img id="loading" src="/static/css/search.gif" />');
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
},true);

document.addEventListener("DOMContentLoaded", function() {
   $('input[name="checkbox-group"]').on('switchChange.bootstrapSwitch', function(event, state) {
      data = {
         type: "group",
         group: $(this).closest('li').attr('gid'),
         state: state
      };
      $.ajax({
         url: "/enlighten",
         global: false,
         type: "POST",
         data:  data,
         cache: "false",
         success: function(response){
            $("[gid='" + data.group + "'] li input").bootstrapSwitch('state', data.state);
         }
      });
   });

   $('input[name="checkbox-light"]').on('switchChange.bootstrapSwitch', function(event, state) {
      data = {
         type: "light",
         light: $(this).closest('li').attr('lid'),
         state: state
      };
      $.ajax({
         url: "/enlighten",
         global: false,
         type: "POST",
         data:  data,
         cache: "false",
         success: function(response) {
            parents = $("li[lid='" + data.light + "']").parents("li[gid]");
            for (var i = 0; i < parents.length; i++) {
               refresh_group_state(parents[i]);
            }
         }
      });
   });
},true);

function refresh_group_state(group) {
   switch_button = $(group).find("input[name='checkbox-group']:first");

   lights = $(group).find("input[name='checkbox-light']");
   off_count = 0
   on_count = lights.length
   for (var i = 0; i < lights.length; i++) {
      if(!$(lights[i]).bootstrapSwitch('state')){
         off_count += 1;
         on_count -= 1;
      }
   }
   if(on_count != 0 && off_count == 0)
      switch_button.bootstrapSwitch('state', true);
   else if (off_count != 0 && on_count == 0)
      switch_button.bootstrapSwitch('state', false);
   else
      switch_button.bootstrapSwitch('indeterminate', true);
}

document.addEventListener("DOMContentLoaded", function() {
   $("#add_group").click(function(){
      $.ajax({
         url: "/new_group",
         global: false,
         type: "POST",
         cache: false,
         success: function(response){
            console.log(response);
            $(".vertical ol").first().append(response);
            $(".edit").editable();
            $("[name='checkbox-group']").bootstrapSwitch('indeterminate', true, true);
         }
      });
   });
},true);

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
