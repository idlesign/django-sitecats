sitecats = {

    /**
     * Application defaults.
     */
    defaults: {
        data_attrs: {
            ties_num: 'tiesnum',
            category_id: 'catid',
            category_separator: 'catsep',
        },
        classes: {
            categories_box: 'categories_box',
            list_entry: 'list_entry',
            choice_box: 'choice_box',
            editor: 'editor',
            choice: 'choice',
        },
        cloud: {
            font_size_min: 10,
            font_size_max: 30,
            font_units: 'px'
        }
    },

    /**
     * Bootstraps various parts of sitecats altogether.
     */
    bootstrap: function() {
        'use strict';

        $(function(){
            sitecats.bootstrap_editors();
        });
    },

    /**
     * Bootstraps category editors.
     *
     * * Hides already chosen categories.
     * * Allows adding categories to a list with a click.
     */
    bootstrap_editors: function() {
        'use strict';

        var cl_list_entry = '.' + this.defaults.classes.list_entry,
            cl_choice_box = '.' + this.defaults.classes.choice_box,
            cl_categories_box = '.' + this.defaults.classes.categories_box,
            cl_editor = '.' + this.defaults.classes.editor,
            cl_choice = '.' + this.defaults.classes.choice,
            attr_cat_id = this.defaults.data_attrs.category_id,
            attr_cat_sep = this.defaults.data_attrs.category_separator;

        $(cl_categories_box).on('click', ' ' + cl_editor + ' ' + ' ' + cl_choice, function() {
            var $cat = $(this),
                form = $cat.parents(cl_editor).eq(0),
                $input = $('input[name="category_title"]', form),
                val_old = $input.val(),
                val_new = $cat.text(),
                category_separator = $input.data(attr_cat_sep);

            if (category_separator !== 'None') {
                category_separator = category_separator + ' ';
                val_new = $.trim(val_old)
                if (val_new) {
                    val_new = val_new.split(category_separator);
                } else {
                    val_new = [];
                }
                val_new.push($cat.text());
                val_new = $.trim(val_new.join(category_separator));
            }

            $input.val(val_new)
        });

        $(cl_categories_box).each(function(idx, cat_box){
            var already_chosen = [];

            if (!$(cl_editor, cat_box).length) {
                return;
            }

            $(cl_list_entry, cat_box).each(function(idx, list_entry){
                already_chosen.push($(list_entry).data(attr_cat_id));
            });

            if (already_chosen.length) {
                $(cl_choice, $(cl_choice_box, cat_box)).each(function (idx, choice) {
                    var $choice = $(choice);

                    if ($.inArray($choice.data(attr_cat_id), already_chosen) > -1) {
                        $choice.hide();
                    }
                });
            }
        });

    },

    /**
     * Creates categories (tags) cloud.
     *
     * @param target_el_id An ID of HTML element containing categories.
     * @param font_size_min Minimum font size.
     * @param font_size_max Maximum font size.
     * @param font_size_units Font size units (px, pt, em, etc.).
     */
    make_cloud: function(target_el_id, font_size_min, font_size_max, font_size_units) {
        'use strict';

        var ties_max,
            ties_min,
            ties_range,
            ties_nums = [],
            ties_num_attr = this.defaults.data_attrs.ties_num,
            font_size_increment = 1,
            selector = '.' + this.defaults.classes.categories_box + ' .' + this.defaults.classes.list_entry,
            $entries = $(selector, '#' + target_el_id);

        $entries.each(function(idx, item){ ties_nums.push($(item).data(ties_num_attr)) });

        if (ties_nums.length < 1) {
            return;
        }

        if (font_size_min===undefined) {
            font_size_min = this.defaults.cloud.font_size_min;
        }

        if (font_size_max===undefined) {
            font_size_max = this.defaults.cloud.font_size_max;
        }

        if (font_size_units===undefined) {
            font_size_units = this.defaults.cloud.font_units;
        }

        ties_nums.sort(function(a, b) { return a - b });
        ties_min = ties_nums[0];
        ties_max = ties_nums.pop();
        ties_range = ties_max - ties_min;
        ties_range = ties_range ? ties_range : 1;
        font_size_increment = (font_size_max - font_size_min) / ties_range;

        $entries.each(function(idx, item){
            var $item = $(item),
                ties_num = $item.data(ties_num_attr),
                font_size = font_size_min + ((ties_num-ties_min) * font_size_increment);

            $item.css('font-size', font_size + font_size_units);
        });

    }

};
