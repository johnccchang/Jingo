/**
 * Author: Jiankai Dang
 * Date: 4/25/13
 * Time: 11:49 PM
 */
$(function () {
    var headingClass = ".accordion-heading", profileContainer = $("#accordion2").on("click", ".update-state",function () {
        var heading = $(this).closest(headingClass);
        heading.find("a").hide();
        heading.find("input").show().focus();
    }).on("blur", "input",function () {
            var heading = $(this).closest(headingClass);
            heading.find("a").show();
            var stateNameInput = heading.find("input:text").hide(), stateName = stateNameInput.val();
            $.post("/tasks/updateState/", {
                uid: heading.attr("data-uid"),
                stateid: heading.attr("data-state-id"),
                state_name: stateName
            }, function (response) {
                if (response.result) {
                    heading.find("span").html(stateName);
                }
            }, "json");
        }).on("click", ".remove-state",function () {
            var heading = $(this).closest(headingClass);
            $.post("/tasks/deleteState/", {
                uid: heading.attr("data-uid"),
                stateid: heading.attr("data-state-id")
            }, function () {
                heading.closest(".accordion-group").remove();
            }, "json");
        }).on("click", ".accordion-group>input",function () {
            profileContainer.find(".current-state").removeClass("current-state").next(".collapse").collapse("hide");
            $(this).next(".accordion-heading").addClass("current-state").next(".collapse").collapse("show");
        }).on("click", ".set-current-state",function () {
            $.post("/tasks/setDefaultState/", {
                uid: uid,
                stateid: $(this).val()
            })
        }).on("click", ".add-tag",function () {
            var sysTagLi = $(this).closest("li"), newTagLi = $('<li><input type="text" required></li>').prependTo(sysTagLi.find("ul"));
            newTagLi.find("input").blur(function () {
                var tagName = $(this).val(), stateid = $(this).closest(".accordion-group").attr("data-stateid"), tagid = sysTagLi.attr("data-tagid");
                $.post("/tasks/addTag/", {
                    uid: uid,
                    sys_tagid: tagid,
                    tag_name: tagName
                }, function (response) {
                    var tagid = response.tagid;
                    newTagLi.html('<label class="checkbox"><input type="checkbox" value="' + tagid + '">' + tagName +
                        '<a class="pull-right update-filter" data-toggle="modal" href="/tasks/getFilter/?uid=' + uid +
                        '&stateid=' + stateid + '&tagid=' + tagid +
                        '" data-target="#myModal"><i class="icon-pencil"></i></a></label>').attr("data-tagid", tagid);
                })
            });
        }).on("click", ".remove-tag",function () {
            var tagLi = $(this).closest("li");
            $.post("/tasks/deleteTag/", {
                uid: uid,
                tagid: tagLi.attr("data-tagid")
            }, function () {
                tagLi.remove();
            })
        }).on("click", ".update-filter", function () {

        }), uid = profileContainer.attr("data-uid");
    $("#addState").click(function () {
        $('<div class="accordion-group"></div>').prependTo(profileContainer).load("/tasks/addState/", {
            uid: uid
        }, function () {
            $(this).find(".update-state").click();
            profileContainer.find(".collapse.in").collapse("hide");
            $(this).find(".collapse").collapse("show");
        });
    });
    $("#editState").click(function () {
        $(this).closest(".btn-toolbar").addClass("edit-state");
        profileContainer.addClass("edit-state");
    });
    $("#doneState").click(function () {
        $(this).closest(".btn-toolbar").removeClass("edit-state");
        profileContainer.removeClass("edit-state");
    });
    $("#updateFilter").click(function () {
        $.post("/tasks/updateFilter/", $("#filterForm").serialize())
    });
})
;