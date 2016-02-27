document.addEventListener("DOMContentLoaded", function() {
   var commandButtons = document.querySelectorAll(".command");
   for (var i=0, l=commandButtons.length; i<l; i++) {
      var button = commandButtons[i];
      button.addEventListener("click", function(e) {
         var clickedButton = e.target;
         var command = clickedButton.value;
         command = command.split("|");
         var sentData = {
            'command' : command[0],
            'mac'     : command[1]
         };
         $.ajax({
            type: 'POST',
            url: '/buttons_proc',
            data: JSON.stringify(sentData,null,'\t'),
            contentType: 'application/json;charset=UTF-8',
            success:function(response){
               console.log(response);
            },
            error: function(error) {
               console.log(error);
            }
         });
      });
   }
}, true);

document.addEventListener("DOMContentLoaded", function() {
   var switches = document.querySelectorAll("checkbox-light");
   console.log(switches);
   for (var i=0, l=switches.length; i<l; i++) {
      var current_switch = switches[i];
      current_switch.addEventListener('change',function(e) {
         // something happens when we change a checkbox!
      });
   }
},true);

document.addEventListener("DOMContentLoaded", function() {
   $("#add_devices").click(function(){
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
            console.log(response);
            console.log(data.group);
            var c = $("[gid='" + data.group + "'] li ");
            for (var i = 0; i < c.length; i++){
               console.log(c);
               c.find('span').addClass('checked');
            }
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
         success: function(response){
            console.log(response);
         }
      });
   });
},true);

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
