$(document).ready(function() {

     
    $('#products_list_view').hide();
    $('#products_grid_button').hide();

    $('#products_list_button').click(function (){
	$('#products_list_view').show();
	$('#products_grid_view').hide();
	$('#products_grid_button').show();
	$('#products_list_button').hide();
    });

    $('#products_grid_button').click(function (){
        $('#products_grid_view').show();
        $('#products_list_view').hide();
	$('#products_list_button').show();
        $('#products_grid_button').hide();	
    });


});
