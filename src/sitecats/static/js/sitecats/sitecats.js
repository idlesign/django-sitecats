window.sitecats = window.sitecats || {

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

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                sitecats.bootstrap_editors();
            });
        } else {
            sitecats.bootstrap_editors();
        }
    },

    /**
     * Bootstraps category editors.
     *
     * * Hides already chosen categories.
     * * Allows adding categories to a list with a click.
     */
    bootstrap_editors: function() {
        'use strict';

        var classes = this.defaults.classes,
            attrs = this.defaults.data_attrs;

        document.querySelectorAll('.' + classes.categories_box).forEach(function(cat_box) {

            cat_box.addEventListener('click', function(event) {
                var choice = event.target.closest('.' + classes.editor + ' .' + classes.choice);

                if (!choice) {
                    return;
                }

                var editor = choice.closest('.' + classes.editor),
                    input = editor.querySelector('input[name="category_title"]'),
                    val_new = choice.textContent,
                    category_separator = input.dataset[attrs.category_separator];

                if (category_separator !== 'None') {
                    category_separator = category_separator + ' ';
                    val_new = input.value.trim();

                    if (val_new) {
                        val_new = val_new.split(category_separator);
                    } else {
                        val_new = [];
                    }

                    val_new.push(choice.textContent);
                    val_new = val_new.join(category_separator).trim();
                }

                input.value = val_new;
            });

            var editor = cat_box.querySelector('.' + classes.editor);

            if (!editor) {
                return;
            }

            var already_chosen = [];

            cat_box.querySelectorAll('.' + classes.list_entry).forEach(function(list_entry) {
                already_chosen.push(list_entry.dataset[attrs.category_id]);
            });

            if (already_chosen.length) {
                cat_box.querySelectorAll('.' + classes.choice_box + ' .' + classes.choice).forEach(function(choice) {
                    if (already_chosen.indexOf(choice.dataset[attrs.category_id]) > -1) {
                        choice.style.display = 'none';
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

        var ties_nums = [],
            ties_num_attr = this.defaults.data_attrs.ties_num,
            selector = '#' + target_el_id + ' .' + this.defaults.classes.categories_box + ' .' + this.defaults.classes.list_entry,
            entries = document.querySelectorAll(selector);

        entries.forEach(function(entry) {
            ties_nums.push(Number(entry.dataset[ties_num_attr]));
        });

        if (ties_nums.length < 1) {
            return;
        }

        if (font_size_min === undefined) {
            font_size_min = this.defaults.cloud.font_size_min;
        }

        if (font_size_max === undefined) {
            font_size_max = this.defaults.cloud.font_size_max;
        }

        if (font_size_units === undefined) {
            font_size_units = this.defaults.cloud.font_units;
        }

        ties_nums.sort(function(a, b) { return a - b; });

        var ties_min = ties_nums[0],
            ties_max = ties_nums[ties_nums.length - 1],
            ties_range = (ties_max - ties_min) || 1,
            font_size_increment = (font_size_max - font_size_min) / ties_range;

        entries.forEach(function(entry) {
            var ties_num = Number(entry.dataset[ties_num_attr]),
                font_size = font_size_min + ((ties_num - ties_min) * font_size_increment);

            entry.style.fontSize = font_size + font_size_units;
        });

    }

};
