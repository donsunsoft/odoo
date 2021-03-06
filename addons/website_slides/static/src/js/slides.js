/*global $, openerp, _, PDFJS */
$(document).ready(function () {

    "use strict";

    var website = openerp.website;
    var _t = openerp._t;
    var widget_parent = $('body');

    website.slide =  {};
    website.slide.page_widgets = {};

    $("timeago.timeago").each(function (index, el) {
        var datetime = $(el).attr('datetime'),
            datetime_obj = openerp.str_to_datetime(datetime),
            // if presentation 7 days, 24 hours, 60 min, 60 second, 1000 millis old(one week)
            // then return fix formate string else timeago
            display_str = "";
        if (datetime_obj && new Date().getTime() - datetime_obj.getTime() > 7 * 24 * 60 * 60 * 1000) {
            display_str = datetime_obj.toDateString();
        } else {
            display_str = $.timeago(datetime_obj);
        }
        $(el).text(display_str);
    });

    /*
     * Like/Dislike Buttons Widget
     */
    website.slide.LikeButton = openerp.Widget.extend({
        setElement: function($el){
            this._super.apply(this, arguments);
            this.$el.on('click', this, _.bind(this.apply_action, this));
        },
        apply_action: function(ev){
            var button = $(ev.currentTarget);
            var slide_id = button.data('slide-id');
            var user_id = button.data('user-id');
            var is_public = button.data('public-user');
            var href = button.data('href');
            if(is_public){
                this.popover_alert(button, _.str.sprintf(_t('Please <a href="/web?redirect=%s">login</a> to vote this slide'), (document.URL)));
            }else{
                var target = button.find('.fa');
                if (localStorage['slide_vote_' + slide_id] !== user_id.toString()) {
                    openerp.jsonRpc(href, 'call', {slide_id: slide_id}).then(function (data) {
                        target.text(data);
                        localStorage['slide_vote_' + slide_id] = user_id;
                    });
                } else {
                    this.popover_alert(button, _t('You have already voted for this slide'));
                }
            }
        },
        popover_alert: function($el, message){
            $el.popover({
                trigger: 'focus',
                placement: 'bottom',
                container: 'body',
                html: true,
                content: function(){
                    return message;
                }
            }).popover('show');
        },
    });

    website.slide.page_widgets['likeButton'] = new website.slide.LikeButton(widget_parent).setElement($('.oe_slide_js_like'));
    website.slide.page_widgets['dislikeButton'] = new website.slide.LikeButton(widget_parent).setElement($('.oe_slide_js_unlike'));

    /*
     * Embedded Code Widget
     */
    website.slide.SlideSocialEmbed = openerp.Widget.extend({
        events: {
            'change input' : 'change_page',
        },
        init: function(parent, max_page){
            this._super(parent);
            this.max_page = max_page || false;
        },
        change_page: function(ev){
            ev.preventDefault();
            var input = this.$('input');
            var page = parseInt(input.val());
            if (this.max_page && !(page > 0 && page <= this.max_page)) {
                page = 1;
            }
            this.update_embedded_code(page);
        },
        update_embedded_code: function(page){
            var embed_input = this.$('.slide_embed_code');
            var new_code = embed_input.val().replace(/(page=).*?([^\d]+)/, '$1' + page + '$2');
            embed_input.val(new_code);
        },
    });

    $('iframe').ready(function() {
        // TODO : make it work. For now, once the iframe is loaded, the value of #page_count is
        // still now set (the pdf is still loading)
        var max_page = $('iframe').contents().find('#page_count').val();
        var slide_social_embed = new website.slide.SlideSocialEmbed($(this), max_page).setElement($('.oe_slide_js_embed_code_widget'));
    });


    /*
     * Send by email Widget
     */
    website.slide.ShareMail = openerp.Widget.extend({
        events: {
            'click button' : 'send_mail',
        },
        send_mail: function(ev){
            var self = this;
            var input = this.$('input');
            var slide_id = this.$('button').data('slide-id');
            if(input.val() && input[0].checkValidity()){
                this.$el.removeClass('has-error');
                openerp.jsonRpc('/slides/slide/send_share_email', 'call', {
                    slide_id: slide_id,
                    email: input.val(),
                }).then(function () {
                    self.$el.html($('<div class="alert alert-info" role="alert"><strong>Thank you!</strong> Mail has been sent.</div>'));
                });
            }else{
                this.$el.addClass('has-error');
                input.focus();
            }
        },
    });

    website.slide.page_widgets['share_mail'] = new website.slide.ShareMail(widget_parent).setElement($('.oe_slide_js_share_email'));

    /*
     * Social Sharing Statistics Widget
     */
    if ($('div#statistic').length) {
        var socialgatter = function (app_url, url, callback) {
            $.ajax({
                url: app_url + url,
                dataType: 'jsonp',
                success: callback
            });
        };
        var current_url = window.location.origin + window.location.pathname;
        socialgatter('https://www.linkedin.com/countserv/count/share?url=', current_url, function (data) {
            $('#linkedin-badge').text(data.count || 0);
            $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#linkedin-badge').text()));
        });
        socialgatter('https://cdn.api.twitter.com/1/urls/count.json?url=', current_url, function (data) {
            $('#twitter-badge').text(data.count || 0);
            $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#twitter-badge').text()));
        });
        socialgatter('https://graph.facebook.com/?id=', current_url, function (data) {
            $('#facebook-badge').text(data.shares || 0);
            $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#facebook-badge').text()));
        });

        $.ajax({
            url: 'https://clients6.google.com/rpc',
            type: "POST",
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify([{
                "method": "pos.plusones.get",
                "id": "p",
                "params": {
                    "nolog": true,
                    "id": current_url,
                    "source": "widget",
                    "userId": "@viewer",
                    "groupId": "@self"
                },
                // TDE NOTE: should there be a key here ?
                "jsonrpc": "2.0",
                "apiVersion": "v1"
            }]),
            success: function (data) {
                $('#google-badge').text(data[0].result.metadata.globalCounts.count || 0);
                $('#total-share').text(parseInt($('#total-share').text()) + parseInt($('#google-badge').text()));
            },
        });
    }
});
