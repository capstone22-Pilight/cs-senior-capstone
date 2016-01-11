document.addEventListener("DOMContentLoaded", function() {
   var commandButtons = document.querySelectorAll(".command");
   for (var i=0, l=commandButtons.length; i<l; i++) {
      var button = commandButtons[i];
      button.addEventListener("click", function(e) {
         e.preventDefault();

         var clickedButton = e.target;
         var command = clickedButton.value;

         var request = new XMLHttpRequest();
         request.onload = function() {
            console.log(request.responseText);
         };
         request.open("GET", "/buttons/" + command, true);
         request.send();
      });
   }
}, true);
