require(["dojo/Deferred", "dojo/_base/array", 'dijit/registry', 'dojo/_base/unload', "dojo/hash", "dojo/query",
        "dojo/dom-class", "dojo/dom-style", "dojo/dom-attr", "dojo/dom-construct", "dojo/dom", "dojo/on",
        "dojo/NodeList-traverse", 'dojo/domReady!'],
        function (Deferred, Array, registry, baseUnload, hash, query, domClass, domStyle,
                  domAttr, domConstruct, dom, on) {

            var unLoad = function() {
                Array.forEach(registry.toArray(), function(item) {
                    item.destroyRecursive();
                });
            };
            baseUnload.addOnUnload(unLoad);

            var request_hash = hash();
            if (request_hash) {
                hash(request_hash);
            } else {
                hash("home");
            }
            // disable the loader gif
            var node = query(".loader")[0];
            domClass.remove(node, 'is-active');

            var footer_links = query("footer li");
            Array.forEach(footer_links, function (e) {
                domClass.add(e, "font-size--3");
            });

            var panel_btn = dom.byId('_file_type_handle');
            var panel_btn2 = dom.byId('_doc_type_handle');
            var panel_btn3 = dom.byId('_map_handle');
            var panel_btn4 = dom.byId('_edit_handle');
            var panel_btn5 = dom.byId('_batch_edit_handle');

            var slider_panel = dom.byId('_slider_panel');

            var file_type_html = dom.byId('_file_type_group');
            var doc_type_html = dom.byId('_doc_type_group');
            var map_html = dom.byId('_map_group');

            var _container = dom.byId('_container');
            var update_panel = dom.byId('_update_panel');

            // add the DRF class names to the django fieldWrapper to get the calendar
            Array.forEach(query('.fieldWrapper'), function(e) {
                domClass.add(e, 'form-group');
            });

            Array.forEach(query('.fieldWrapper input'), function(e) {
                domClass.add(e, 'form-control');
            });

            // make the multi-select boxes side by side
            Array.forEach(query('.fieldWrapper > select').parent(), function(e) {
                domClass.add(e, 'inline');
            });

            Array.forEach(query('.fieldWrapper > ul').parent(), function(e) {
                domClass.add(e, 'inline-list');
            });


            // disable the click event for the dropdown buttons in the update panel
            Array.forEach(query('button.accordion'), function(e) {
                on(e, 'click', function(evt) {
                    evt.preventDefault();
                    domClass.toggle(e, "active");
                    var panel = e.nextElementSibling;
                    if (domClass.contains(panel, "active")) {
                        domClass.replace(panel, "off", "active")
                    } else {
                        domClass.replace(panel, "active", "off");
                    }
                });
            });

            var check_panel = function(event) {

                var deferred = new Deferred();
                var target = event.target;
                // if the slider panel is not open, open it.
                 if (!domClass.contains(slider_panel, "open") && !domClass.contains(slider_panel, "open_from_trans")
                 && !domClass.contains(slider_panel, "close_to_trans")) {
                    domClass.replace(slider_panel, "open", "close");

                    // if the target button is for map, add then set the map class
                     if (target === panel_btn3) {
                         domClass.replace(slider_panel, "open_from_trans", "close_map");
                     }
                     domClass.remove(slider_panel, "close_map");
                    domClass.remove(event.target, 'btn-clear');
                    deferred.resolve(slider_panel);
                } else {
                     // the panel is already open; if the button is not clear, close the panel, and make button clear.
                     console.log(event.target);
                     if (!domClass.contains(event.target, 'btn-clear')) {
                         domClass.replace(slider_panel, "close", "open");
                         domClass.replace(slider_panel, "close", "close_to_trans");
                         // if the target button is for map, add the close map class
                         if (event.target === panel_btn3) {
                             domClass.replace(slider_panel, "close_map", "open_map");
                             domClass.replace(slider_panel, "close_map", "open_from_trans");
                         }
                         domClass.add(event.target, 'btn-clear');
                     } else {
                         // the panel is open and the button is clear, keep the panel open, make other buttons clear
                         // make this button blue
                         Array.forEach([panel_btn, panel_btn2, panel_btn3], function(btn) {
                             if (btn !== target) {
                                 domClass.add(btn, 'btn-clear');
                             }
                         });

                         if (panel_btn === target || panel_btn2 === target) {
                             // one of the file type buttons was clicked and the slider panel needs to move to this location
                             // from either the closed position or the open_map position.
                            if (domClass.contains(slider_panel, 'open_map')) {
                                // the map is open to 100%
                                // move it to the width of the file type panels
                                domClass.replace(slider_panel, 'close_to_trans', 'open_map');

                            } else if (domClass.contains(slider_panel, 'open_from_trans')) {
                                domClass.replace(slider_panel, 'close_to_trans', 'open_from_trans')
                            }
                         } else if (panel_btn3 === target) {
                             // open the slider panel to the full extent from the file_type width
                             if (domClass.contains(slider_panel, 'open') || domClass.contains(slider_panel, 'close_to_trans')) {
                                 domClass.replace(slider_panel, 'open_from_trans', 'open');
                                 domClass.replace(slider_panel, 'open_from_trans', 'close_to_trans');
                             }
                         }
                         domClass.remove(event.target, 'btn-clear');
                     }
                     deferred.resolve(slider_panel);
                 }

                return deferred.promise;
            };

            on(panel_btn, 'click', function(event) {
                event.preventDefault();
                check_panel(event).then(function(e) {
                    domClass.remove(doc_type_html, "visible");
                    domClass.remove(map_html, "visible");
                    domClass.toggle(file_type_html, "visible");
                });
            });

            on(panel_btn2, 'click', function(event) {
                event.preventDefault();
                check_panel(event).then(function(e) {
                    domClass.remove(file_type_html, "visible");
                    domClass.remove(map_html, "visible");
                    domClass.toggle(doc_type_html, "visible");
                });
            });

            on(panel_btn3, 'click', function(event) {
                event.preventDefault();
                check_panel(event).then(function(e) {
                    domClass.remove(doc_type_html, "visible");
                    domClass.remove(file_type_html, "visible");
                    domClass.add(map_html, "visible");

                });
            });

            on(panel_btn4, 'click', function(event) {
                event.preventDefault();
                if (domClass.contains(update_panel, 'close')) {
                    domClass.replace(update_panel, 'open', 'close');
                    domClass.replace(_container, 'ropen', 'rclose');
                } else if (domClass.contains(update_panel, 'open')) {
                    domClass.replace(update_panel, 'close', 'open');
                    domClass.replace(_container, 'rclose', 'ropen');
                } else {
                    domClass.add(update_panel, 'open');
                    domClass.add(_container, 'ropen');
                }
            });

            on(panel_btn5, 'click', function(event) {
                event.preventDefault();
            });


            var icons = query('.fileIcon');
            Array.forEach(icons, function(div) {
                on(div, 'click', function(evt) {
                    console.log(evt);
                    // get all data-atts on the icon and place data in the update form
                    var file_id = domAttr.get(div, 'data-file-id');
                    var date_added = domAttr.get(div, 'data-file-date-added');
                    var file_path = domAttr.get(div, 'data-file-path');
                    var base_name = domAttr.get(div, 'data-file-base-name');
                    var grid_cells = domAttr.get(div, 'data-file-grid-cells');
                    var project_title = domAttr.get(div, 'data-file-project-title');
                    var project_desc = domAttr.get(div, 'data-file-project-desc');
                    var project_date = domAttr.get(div, 'data-file-project-date');
                    var sheet_title = domAttr.get(div, 'data-file-sheet-title');
                    var sheet_type = domAttr.get(div, 'data-file-sheet-type');
                    var doc_type = domAttr.get(div, 'data-file-doc-type');
                    var sheet_desc = domAttr.get(div, 'data-file-sheet-desc');
                    var vendor = domAttr.get(div, 'data-file-vendor');
                    var discipline = domAttr.get(div, 'data-file-discipline');
                    var airport = domAttr.get(div, 'data-file-airport');
                    var funding_type = domAttr.get(div, 'data-file-funding-type');
                    var grant_number = domAttr.get(div, 'data-file-grant-number');

                    // populate the edit form with these values
                    if (!domClass.contains(update_panel, 'open')) {
                        on.emit(panel_btn4, "click", {
                            bubbles: true,
                            cancelable: true
                        });
                    }

                    dom.byId('id_edit_id').value = file_id;

                    dom.byId('id_edit_base_name').value = base_name;

                    dom.byId('id_edit_grid_cells').value = grid_cells;

                    if (sheet_title === "None") {
                        sheet_title = ""
                    }

                    dom.byId('id_edit_sheet_title').value = sheet_title;

                    Array.forEach(query("#id_edit_discipline input"), function(box) {
                        box.checked = false;
                    });
                    Array.forEach(discipline.split(","), function(e) {
                        Array.some(query("#id_edit_discipline input"), function(input) {
                            if (input.value === e) {
                                input.checked = true;
                            }
                        });
                    });
                    Array.forEach(query("#id_edit_sheet_type input"), function(box) {
                        box.checked = false;
                    });
                    Array.forEach(sheet_type.split(","), function(e) {
                        Array.some(query("#id_edit_sheet_type input"), function(input) {
                            if (input.value === e) {
                                input.checked = true;
                            }
                        });
                    });
                     Array.forEach(query("#id_edit_doc_type input"), function(box) {
                        box.checked = false;
                    });
                    Array.forEach(doc_type.split(","), function(e) {
                        Array.some(query("#id_edit_doc_type input"), function (input) {
                            if (input.value === e) {
                                input.checked = true;
                            }
                        });
                    });

                    if (project_title === "None") {
                        project_title = ""
                    }

                    dom.byId('id_edit_project_title').value = project_title;

                    if (project_desc === "None") {
                        project_desc = "";
                    }

                    dom.byId('id_edit_project_desc').value = project_desc;

                    if (project_date === "None") {
                        project_date = null;
                    }

                    dom.byId('id_edit_project_date').value = project_date;

                    if (sheet_desc === "None") {
                        sheet_desc = "";
                    }

                    dom.byId('id_edit_sheet_desc').value = sheet_desc;

                    if (vendor === "None") {
                        vendor = "";
                    }

                    dom.byId('id_edit_vendor').value = vendor;

                    if (funding_type === "None") {
                        funding_type = "";
                    }

                    dom.byId('id_edit_funding_type').value = funding_type;

                    Array.forEach(query("#id_edit_airport input"), function(e) {
                        if (e.value === airport) {
                            e.checked = true;
                        }
                    });

                    dom.byId('id_edit_date_added').value = date_added;

                    dom.byId('id_edit_file_path').value = file_path;

                    if (grant_number === "None") {
                        grant_number = "";
                    }

                    dom.byId('id_edit_grant_number').value = grant_number;

                });
            });
        });