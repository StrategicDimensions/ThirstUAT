$(document).ready(function () {
    $(window).scroll(function () {
        if ($(window).scrollTop() >= $(document).height() - $(window).height() - 300) {
            $('#beverages_float').css('max-height', '200px').css('top', '50px');
        } else {
            $('#beverages_float').css('max-height', '1000px').css('top', '120px');
        }

    });

    function view_mode_list() {
        var url = '/products/view/list';

        jQuery.ajax({
            url: url,
            type: 'POST',
            data: {},
            success: function (response) {
                response = jQuery.parseJSON(response);
                if (response.flag === 1) {
                    window.location.reload();
                }
            }
        });
    }
    window.view_mode_list = view_mode_list;

    function view_mode_grid() {
        var url = '/products/view/grid';

        jQuery.ajax({
            url: url,
            type: 'POST',
            data: {},
            success: function (response) {
                response = jQuery.parseJSON(response);
                if (response.flag === 1) {
                    window.location.reload();
                }
            }
        });
    }
    window.view_mode_grid = view_mode_grid;

    function add_product(project_id, bev_menu_product_id, product_id, product_name, sub_categ_id, sub_categ_name,
        prod_type, beverage_id) {

        var url = '/add/' + project_id + '/' + beverage_id + '/' + product_id;

        jQuery.ajax({
            url: url,
            type: 'POST',
            data: {
                bev_menu_product_id: bev_menu_product_id,
                product_id: product_id,
                sub_categ_id: sub_categ_id,
                prod_type: prod_type
            },
            success: function (response) {
                response = jQuery.parseJSON(response);
                if (response.flag === 0) {
                    alert('cannot add more than maximum products for same sub category');
                } else if (response.flag === 1) {
                    //$('#member_table tbody').append("
                    window.location.reload();

                }
            }
        });
    }
    window.add_product = add_product;

    function remove_product(project_id, bev_menu_product_id, product_id, product_name, sub_categ_id, sub_categ_name,
        prod_type, beverage_id) {
        var url = '/remove/' + project_id + '/' + beverage_id + '/' + product_id;
        jQuery.ajax({
            url: url,
            type: 'POST',
            data: {
                bev_menu_product_id: bev_menu_product_id,
                product_id: product_id,
                sub_categ_id: sub_categ_id,
                prod_type: prod_type
            },
            success: function (response) {
                response = jQuery.parseJSON(response);
                if (response.flag === 0) {
                    alert('Error occured on remove product')
                } else if (response.flag === 1) {
                    window.location.reload();
                }
            }
        });
    }
    window.remove_product = remove_product;

    $('.o_next_tab').click(function () {
        var $tab = $('.nav-tabs > .active').next('li').find('a');
        $tab.trigger('click');
        $('html, body').animate({
            scrollTop: $tab.offset().top - 100
        }, 200);
    });

});