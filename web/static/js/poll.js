setInterval(function(){
   var numdevices = 5;
   $.ajax({
      url: "/poll",
      global: false,
      type: "POST",
      cache: false,
      success: function(response){
         console.log(response);
      }});
},3000);
