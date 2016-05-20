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
               if (response[key] == 'False'){
                  state = false;
               }else if (response[key] == 'True'){
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
},1000);

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
            list_item = $("li[lid="+key+"]");
            if (response.hasOwnProperty(key) && !(list_item.find('input:focus').length > 0)) {
               list_item.find('span.edit').editable('setValue', response[key], false);
            }
         }
      }});
},3000)

// Time clock poller
setInterval(function(){
   var name;
   data = {
      data : "clock"
   }
   $.ajax({
      url: "/poll",
      global: false,
      type: "POST",
      cache: false,
      data: data,
      success: function(response){
         $(".time-clock").text(response);
      }});
},1000)

setInterval(function(){
   window.location.reload(1);
},60000)
