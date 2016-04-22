setInterval(function(){
   var numdevices = 5;
   var state;
   $.ajax({
      url: "/poll",
      global: false,
      type: "POST",
      cache: false,
      success: function(response){
         for (var key in response) {
            if (response.hasOwnProperty(key)) {
               switch_button = $("li[lid='" + key + "']").find('input');
               if (response[key] == '0'){
                  state = false;
               }else if (response[key] == '1'){
                  state = true;
               }
               console.log(state);
               switch_button.bootstrapSwitch('state',state);
               state = null;
            }
         }
      }});
},3000);
