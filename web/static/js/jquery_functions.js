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
