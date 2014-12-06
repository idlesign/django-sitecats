sitecats = {

    /**
     * Application defaults.
     */
    defaults: {
        ties_num_data_attr: 'tiesnum',
        list_entry_class: 'list_entry',
        cloud: {
            font_size_min: 10,
            font_size_max: 30,
            font_units: 'px'
        }
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
            ties_num_attr = this.defaults.ties_num_data_attr,
            font_size_increment = 1,
            $entries = $('.' + this.defaults.list_entry_class, '#' + target_el_id);

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
