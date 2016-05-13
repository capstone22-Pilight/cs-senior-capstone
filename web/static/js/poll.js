setInterval(function(){
   var state;
   data = {
      data: "state"
   };
   $.ajax({
      url: "/poll",
      global: false,
      type: "POST",
      cache: false,
      data: data,
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
               if (((switch_button).is(':focus'))!=true){
                  switch_button.bootstrapSwitch('state',state);
               }
               state = null;
            }
         }
      }});
},3000);

// Name change poll, a seperate poller since we want
// different polling times for each type
setInterval(function(){
   var name;
   data = {
      data : "names"
   }
   $.ajax({
      url: "/poll",
      global: false,
      type: "POST",
      cache: false,
      data: data,
      success: function(response){
         for (var key in response) {
            if (response.hasOwnProperty(key)) {
               switch_button = $("span[data-name='" + response[key] + "']");
               console.log(switch_button);
               switch_button.html('ey b0ss');
            }
         }
      }});
},3000)

setInterval(function(){
   window.location.reload(1);
},60000)
