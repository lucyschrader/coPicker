function saveSelection(irn, mediaIrn, selection) {
  var mediaDiv = document.getElementById("block-" + mediaIrn)
  var buttonsDiv = document.getElementById("buttons-" + mediaIrn)
  var selectButton = document.getElementById("select-" + mediaIrn + "-y")
  var deselectButton = document.getElementById("select-" + mediaIrn + "-n")

  selectionButton.style.display = "block";

  var db_data = {"irn": irn, "media_irn": mediaIrn, "selection": selection}

  $.ajax({
   type: "POST",
   url: "/select",
   data: db_data,
   contentType: "application/json",
   dataType: 'json',
   success: function(result) {
    if(selection == "true") {
     selectButton.class = result.rows; 
    }
   } 
 }); 
}