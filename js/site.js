(function (philwc, undefined) {
    var cols = {
        'red': {
            300: '#e57373',
            700: '#d32f2f',
            dark: false
        },
        'pink': {
            300: '#f06292',
            700: '#c2185b',
            dark: false
        },
        'purple': {
            300: '#ba68c8',
            700: '#7b1fa2',
            dark: false
        },
        'deep-purple': {
            300: '#9575cd',
            700: '#512da8',
            dark: false
        },
        'indigo': {
            300: '#7986cb',
            700: '#303f9f',
            dark: false
        },
        'blue': {
            300: '#64b5f6',
            700: '#1976d2',
            dark: false
        },
        'light-blue': {
            300: '#4fc3f7',
            700: '#0288d1',
            dark: false
        },
        'cyan': {
            300: '#4dd0e1',
            700: '#0097a7',
            dark: false
        },
        'teal': {
            300: '#4db6ac',
            700: '#00796b',
            dark: false
        },
        'green': {
            300: '#81c784',
            700: '#388e3c',
            dark: false
        },
        'light-green': {
            300: '#aed581',
            700: '#689f38',
            dark: false
        },
        'lime': {
            300: '#dce775',
            700: '#afb42b',
            dark: true
        },
        'yellow': {
            300: '#fff176',
            700: '#fbc02d',
            dark: true
        },
        'amber': {
            300: '#ffd54f',
            700: '#ffa000',
            dark: true
        },
        'orange': {
            300: '#ffb74d',
            700: '#f57c00',
            dark: false
        },
        'deep-orange': {
            300: '#ff8a65',
            700: '#e64a19',
            dark: false
        },
        'brown': {
            300: '#a1887f',
            700: '#5d4037',
            dark: false
        },
        'grey': {
            300: '#e0e0e0',
            700: '#616161',
            dark: false
        },
        'blue-grey': {
            300: '#90a4ae',
            700: '#455a64',
            dark: false
        }
    };
    var interval;

    philwc.init = function () {
        events();
        setRandomCol();
    };

    function events() {
        $(document).on("keypress", function (e) {
            if (e.ctrlKey && ( e.which === 10)) {
                dialog();
            }

            if (e.ctrlKey && e.which === 127) {
                if (interval) {
                    console.log('Clearing Interval');
                    clearInterval(interval)
                } else {
                    console.log('Setting Interval');
                    interval = setInterval(function () {
                        setRandomCol();
                    }, 10000);
                }
            }
        });

        $(document).on('click', '.col-select', function () {
            if (interval) {
                clearInterval(interval);
            }
            setCol($(this).attr('data-col'));
            $('#dialog').fadeOut(function () {
                $('#dialog').remove();
            });
        });

        $(document).on('click', '#close', function () {
            $('#dialog').fadeOut(function () {
                $('#dialog').remove();
            });
        });
    }

    function setCol(col) {
        if (col in cols) {
            var c = cols[col];
            var $body = $('body');

            if (c['dark']) {
                $body.addClass('dark');
            } else {
                $body.removeClass('dark');
            }
            $body.css('background-color', c[300]);


            $('.cover-container').css('background-color', c[700]);
        }
    }

    function randomCol() {
        var colnames = Object.keys(cols);
        return colnames[Math.floor(Math.random() * colnames.length)];
    }

    function setRandomCol() {
        setCol(randomCol());
    }

    function dialog() {
        if ($('.site-wrapper').find('#dialog').length > 0) {
            return;
        }

        var html = '<div id="dialog" style="display: none; position: absolute; top: 100px; width: 100%; height: 70%; overflow-y: auto; overflow-x: hidden">' +
            '<div class="row">' +
            '<div class="col-md-8 col-md-offset-2">';

        html += '<p class="lead">Select Colour <a href="javascript:void(0);" id="close" style="margin-left: 75%;"><span class="glyphicon glyphicon-remove"></span></a></p><div class="list-group">';

        $.each(cols, function (col, val) {
            var title = col.replace('-', ' ');
            title = title.replace(/^([a-z\u00E0-\u00FC])|\s+([a-z\u00E0-\u00FC])/g, function ($1) {
                return $1.toUpperCase()
            });

            html += '<a class="list-group-item col-select" href="javascript:void(0);" data-col="' + col + '">' + title + '</a>';
        });

        html += '</div></div>' +
            '</div>' +
            '</div>';

        var $html = $(html);
        $('.cover-container').after($html);
        $html.fadeIn();
    }
})(window.philwc = window.philwc || {});

$(document).ready(function () {
    philwc.init();
});

