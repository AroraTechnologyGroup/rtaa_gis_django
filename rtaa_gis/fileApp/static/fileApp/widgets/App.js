define([
  "dojo/Deferred",
  "dojo/_base/lang",
  "dojo/_base/array",
  'dojo/_base/unload',
  "dojo/_base/declare",
  "dojo/request",
  "dojo/mouse",
  "dojo/parser",
  "dojo/cookie",
  "dojo/json",
  "dojo/hash",
  "dojo/query",
  "dojo/topic",
  "dojo/dom-class",
  "dojo/dom-style",
  "dojo/dom-attr",
  "dojo/dom-construct",
  "dojo/dom",
  "dojo/on",
  "dojo/date",

  "esri/geometry/Point",
  "esri/SpatialReference",

  "dojox/widget/Toaster",

  'dijit/registry',
    'dijit/layout/ContentPane',
  "dijit/Calendar",
  "dijit/form/DateTextBox",
  "dijit/Menu",
  "dijit/popup",
  "dijit/MenuItem",
  "dijit/_WidgetBase",

  "dojo/NodeList-traverse",
    ],
    function (
      Deferred,
      lang,
      Array,
      baseUnload,
      declare,
      request,
      mouse,
      parser,
      cookie,
      JSON,
      hash,
      query,
      topic,
      domClass,
      domStyle,
      domAttr,
      domConstruct,
      dom,
      on,
      date,

      Point,
      SpatialReference,

      Toaster,

      registry,
      ContentPane,
      Calendar,
      DateTextBox,
      Menu,
      popup,
      MenuItem,
      _WidgetBase
  ) {

      var panel_btn = dom.byId('_file_type_handle');
      var panel_btn2 = dom.byId('_doc_type_handle');
      var panel_btn3 = dom.byId('_map_handle');
      var panel_btn4 = dom.byId('_attribute_handle');
      var panel_btn5 = dom.byId('_batch_edit_handle');

      var date_added = dom.byId('id_date_added');
      var after_date = dom.byId('id_after_date');
      var before_date = dom.byId('id_before_date');
      var edit_proj_date = dom.byId('id_edit_project_date');

      var slider_panel = dom.byId('_slider_panel');

      var file_type_html = dom.byId('_file_type_group');
      var doc_type_html = dom.byId('_doc_type_group');
      var map_html = dom.byId('_map_group');

      var _container = dom.byId('_container');
      var _result_box = dom.byId('_resultContainer');
      var update_panel = dom.byId('_update_panel');

      var ftype_all = dom.byId('all_file_type_select_all');

      var doctype_all = dom.byId('_doc_type_select_all');

      var edit_disc_all = query('#id_edit_discipline input[value="all"]');
      var edit_sheet_all = query('#id_edit_sheet_type input[value="all"]');
      var edit_doc_all = query('#id_edit_doc_type input[value="all"]');

      var grid_search_list = dom.byId('id_grid_cells');
      var grid_update_list = dom.byId('id_edit_new_grid_cells');

      var previous_link = dom.byId('_page_before');
      var after_link = dom.byId('_page_after');

      var filter_form = dom.byId('_filter_form');

      var btn_accrd = query('button.accordion');
      var icons = query('.icon-container');
      var f_nodes = query('#id_file_type input');
      var d_nodes = query('#id_image_type input');
      var t_nodes = query('#id_table_type input');
      var gis_nodes = query('#id_gis_type input');
      var doc_nodes = query('#id_document_type input');
      var edit_disc_nodes = query('#id_edit_discipline input');
      var edit_sheet_nodes = query('#id_edit_sheet_type input');
      var edit_doc_nodes = query('#id_edit_doc_type input');

      return declare("App", [_WidgetBase], {
        map: null,
        constructor: function() {
          this.inherited(arguments);
        },

        postCreate: function () {
          this.inherited(arguments);
          var self = this;

          var view_menu = self.view_menu = new Menu({
            targetNodeIds: ["_resultBox"],
            selector: ".fileIcon.viewable"
          });

          var non_view_menu = self.non_view_menu = new Menu({
            targetNodeIds: ["_resultBox"],
            selector: ".fileIcon.non-viewable"
          });

          var download_menu_item = function () {
            return new MenuItem({
              label: "Download",
              iconClass: "taskIcon",
              onClick: function (evt) {
                var node = this.getParent().currentTarget;
                var _id = domAttr.get(node, "data-file-id");

                // if not on the local server get the SCRIPT NAME
                var url;
                if (window.location.hostname !== '127.0.0.1') {
                  var script_name = window.location.pathname.split("/")[1];
                  url = window.location.origin + "/" + script_name + "/fileApp/eng-io/" + _id + "/_download/";
                } else {
                  url = window.location.origin + "/fileApp/eng-io/" + _id + "/_download/";
                }
                var a = domConstruct.create("a", {
                  href: url,
                  download: true,
                  withCredentials: true
                });
                // the anchor node has to be added to the dom before the domEvent can be fired
                domConstruct.place(a, "_resultBox");
                a.click();
                domConstruct.destroy(a);
                console.log(_id);
              }
            });
          };

          var view_menu_item = function () {
            return new MenuItem({
              label: "View File",
              onClick: function (evt) {
                var node = this.getParent().currentTarget;
                var _id = domAttr.get(node, "data-file-id");
                // if not on the local server get the SCRIPT NAME
                var url;
                if (window.location.hostname !== '127.0.0.1') {
                  var script_name = window.location.pathname.split("/")[1];
                  url = window.location.origin + "/" + script_name + "/fileApp/eng-io/" + _id + "/_view/";
                } else {
                  url = window.location.origin + "/fileApp/eng-io/" + _id + "/_view/";
                }

                var a = domConstruct.create("a", {
                  href: url,
                  target: "_blank",
                  withCredentials: true
                });
                // the anchor node has to be added to the dom before the domEvent can be fired
                domConstruct.place(a, "_resultBox");
                a.click();
                domConstruct.destroy(a);
              }
            });
          };

          view_menu.addChild(download_menu_item());
          view_menu.addChild(view_menu_item());

          // cloning the Menu Item allows it to be reused
          non_view_menu.addChild(download_menu_item());

          view_menu.startup();
          non_view_menu.startup();

          var added_val;
          var before_val;
          var after_val;
          var edit_proj_val;

          if (!date_added.value) {
            added_val = 0;
          } else {
            added_val = date_added.value;
          }

          if (!before_date.value) {
            before_val = 0;
          } else {
            before_val = before_date.value;
          }

          if (!after_date.value) {
            after_val = 0;
          } else {
            after_val = after_date.value;
          }

          if (!edit_proj_date.value) {
            edit_proj_val = 0;
          } else {
            edit_proj_val = edit_proj_date.value;
          }

          var added_date_box = self.added_date_box = new DateTextBox({
            value: added_val,
            name: "date_added"
          }, date_added).startup();

          var before_date_box = self.before_date_box = new DateTextBox({
            value: before_val,
            name: "before_date"
          }, before_date).startup();

          var after_date_box = self.after_date_box = new DateTextBox({
            value: after_val,
            name: "after_date"
          }, after_date).startup();

          var edit_proj_date_box = self.edit_proj_date_box = new DateTextBox({
            value: edit_proj_val,
            name: "edit_project_date"
          }, edit_proj_date).startup();

          self.setupConnections();
        },

        activateWindow: function(target_pane) {
          var self = this;
          panes = [_result_box, map_html];
          Array.forEach(panes, function(e) {
            if (e !== target_pane) {
              domStyle.set(e, "display", "none");
            } else {
              domStyle.set(e, "display", "block");
            }
          });
        },
        setupConnections: function() {
          var self = this;


          // disable the click event for the dropdown buttons in the update panel
          if (btn_accrd) {
            Array.forEach(btn_accrd, function (e) {
              on(e, 'click', function (evt) {
                evt.preventDefault();
                domClass.toggle(e, "active");
                var panel = e.nextElementSibling;
                if (domClass.contains(panel, "active")) {
                  domClass.replace(panel, "off", "active");
                } else {
                  domClass.replace(panel, "active", "off");
                }
              });
            });
          }

          if (panel_btn) {
            on(panel_btn, 'click', function (event) {
              event.preventDefault();
              self.checkPanel(event).then(function (e) {
                domClass.remove(doc_type_html, "visible");
                domClass.toggle(file_type_html, "visible");
              });
            });
          }

          if (panel_btn2) {
            on(panel_btn2, 'click', function (event) {
              event.preventDefault();
              self.checkPanel(event).then(function (e) {
                domClass.remove(file_type_html, "visible");
                domClass.toggle(doc_type_html, "visible");
              });
            });
          }

          if (panel_btn3) {
            on(panel_btn3, 'click', function (event) {
              event.preventDefault();

              if (domClass.contains(map_html, "open_map")) {
                domClass.replace(map_html, "close_map", "open_map");
                setTimeout(function() {
                  self.activateWindow(_result_box);
                }, 1000);
              } else if (domClass.contains(map_html, "close_map")) {
                domClass.replace(map_html, "open_map", "close_map");
                setTimeout(function() {
                  self.activateWindow(map_html);
                }, 1000);
              } else {
                domClass.add(map_html, "open_map");
                setTimeout(function() {
                  self.activateWindow(map_html);
                }, 1000);
              }

              domClass.toggle(panel_btn3, 'btn-clear');
            });
          }

          if (panel_btn4) {
            on(panel_btn4, 'click', function (event) {
              event.preventDefault();
              // open the file attribute viewer

              domClass.toggle(panel_btn4, 'btn-clear');

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
          }

          if (panel_btn5) {
            on(panel_btn5, 'click', function(event) {
                event.preventDefault();
            });
          }

          if (icons) {
            Array.forEach(icons, function (div) {
              // get the icon-image node child and fileIcon div
              // get all data-atts on the icon and place data in the update form
              var file_icon = query(".fileIcon", div)[0];
              var icon_image = query(".icon-image", div)[0];


              var file_id = domAttr.get(file_icon, 'data-file-id');
              var date_added = domAttr.get(file_icon, 'data-file-date-added');
              var file_path = domAttr.get(file_icon, 'data-file-path');
              var base_name = domAttr.get(file_icon, 'data-file-base-name');
              var grid_cells = domAttr.get(file_icon, 'data-file-grid-cells');
              var project_title = domAttr.get(file_icon, 'data-file-project-title');
              var project_desc = domAttr.get(file_icon, 'data-file-project-desc');
              var project_date = domAttr.get(file_icon, 'data-file-project-date');
              var sheet_title = domAttr.get(file_icon, 'data-file-sheet-title');
              var sheet_type = domAttr.get(file_icon, 'data-file-sheet-type');
              var doc_type = domAttr.get(file_icon, 'data-file-doc-type');
              var sheet_desc = domAttr.get(file_icon, 'data-file-sheet-desc');
              var vendor = domAttr.get(file_icon, 'data-file-vendor');
              var discipline = domAttr.get(file_icon, 'data-file-discipline');
              var airport = domAttr.get(file_icon, 'data-file-airport');
              var funding_type = domAttr.get(file_icon, 'data-file-funding-type');
              var grant_number = domAttr.get(file_icon, 'data-file-grant-number');

              var toast_node = query("#_"+file_id+"_toast");
              var myToaster = new Toaster({id: '_'+file_id+'_toast'}, toast_node[0]);

              var table_div = domConstruct.create("div", {"class": "overflow-auto _table_container"});
              var _table = domConstruct.create("table", {"class": 'table-striped table-blue'}, table_div);
              var head = domConstruct.create("thead", null, _table);
              var header_row = domConstruct.create("tr", null, head);
              var column_1 = domConstruct.create("th", {"innerHTML": "Field Name"}, header_row);
              var column_2 = domConstruct.create("th", {"innerHTML": "Value"}, header_row, "last");

              var tbody = domConstruct.create("tbody", null, _table);

              if (project_title && project_title !== "None") {
                let _row = domConstruct.create("tr", null, tbody);
                let td1 = domConstruct.create("td", {"innerHTML": "Project Title", "class": "text-off-black"}, _row);
                let td2 = domConstruct.create("td", {"innerHTML": project_title, "class": "text-green"}, _row, "last");
              }

              if (project_date && project_date !== "None") {
                let _row = domConstruct.create("tr", null, tbody);
                let td1 = domConstruct.create("td", {"innerHTML": "Project Date", "class": "text-off-black"}, _row);
                let td2 = domConstruct.create("td", {"innerHTML": project_date, "class": "text-green"}, _row, "last");
              }
              if (sheet_title && sheet_title !== "None") {
                let _row = domConstruct.create("tr", null, tbody);
                let td1 = domConstruct.create("td", {"innerHTML": "Sheet Title", "class": "text-off-black"}, _row);
                let td2 = domConstruct.create("td", {"innerHTML": sheet_title, "class": "text-green"}, _row, "last");
              }
              if (discipline && discipline !== "None") {
                let _row = domConstruct.create("tr", null, tbody);
                let td1 = domConstruct.create("td", {"innerHTML": "Discipline", "class": "text-off-black"}, _row);
                let td2 = domConstruct.create("td", {"innerHTML": discipline, "class": "text-green"}, _row, "last");
              }
              if (base_name && base_name !== "None") {
                let _row = domConstruct.create("tr", null, tbody);
                let td1 = domConstruct.create("td", {"innerHTML": "File Name", "class": "text-off-black"}, _row);
                let td2 = domConstruct.create("td", {"innerHTML": base_name, "class": "text-green"}, _row, "last");
              }
              if (date_added && date_added !== "None") {
                let _row = domConstruct.create("tr", null, tbody);
                let td1 = domConstruct.create("td", {"innerHTML": "Date Added", "class": "text-off-black"}, _row);
                let td2 = domConstruct.create("td", {"innerHTML": date_added, "class": "text-green"}, _row, "last");
              }

              myToaster.setContent(table_div.innerHTML);
              myToaster.hide();

              on(div, mouse.enter, function(evt) {
                domClass.add(div, "hover-div");
                domClass.add(icon_image, "hover-image");
                domClass.add(file_icon, "hover-file");

                myToaster.show();
              });
              on(div, mouse.leave, function(evt) {
                domClass.remove(div, "hover-div");
                domClass.remove(file_icon, "hover-file");
                domClass.remove(icon_image, "hover-image");
                // myToaster.setContent("");
                myToaster.hide();
              });

              on(div, 'click', function (evt) {
                console.log(evt);
                // close the context menu
                Array.forEach([self.view_menu, self.non_view_menu], function (e) {
                  popup.close(e);
                });

                if (mouse.isLeft(evt)) {
                  // TODO -to allow for multiple selection a table must be used to render results
                  // right click is handled by the Menu Popup
                  var nodes = query(".selected-file", _result_box);
                  if (nodes) {
                    // check if the clicked file is already selected
                    var should_disable = Array.some(nodes, function (e) {
                      return (e === file_icon);
                    });

                    if (should_disable) {
                      domClass.remove(file_icon, "selected-file");
                      domClass.remove(icon_image, "selected-image");
                    } else {
                      Array.forEach(nodes, function(node) {
                        // disable all other selected files; there currently can be only one selected file
                        domClass.remove(node, "selected-file");
                        domClass.remove(icon_image, "selected-image");
                      });
                      domClass.add(file_icon, "selected-file");
                      domClass.add(icon_image, "selected-image");
                    }
                  } else {
                    domClass.add(file_icon, "selected-file");
                    domClass.add(icon_image, "selected-image");
                  }


                  // open the attribute form
                  // if (!domClass.contains(update_panel, 'open')) {
                  //   on.emit(panel_btn4, "click", {
                  //     bubbles: true,
                  //     cancelable: true
                  //   });
                  // }

                  dom.byId('id_edit_id').value = file_id;

                  dom.byId('id_edit_base_name').value = base_name;

                  // empty the div of grid cells
                  var edit_grid_list = dom.byId("id_edit_grid_cells");
                  domConstruct.empty(edit_grid_list);
                  // add checkbox and label for each grid cell
                  if (grid_cells) {
                    Array.forEach(grid_cells.split(","), function (e) {

                      var li = domConstruct.create("li");
                      var label = domConstruct.create("label", {"for": e + "_id", innerHTML: e});
                      var input = domConstruct.create("input", {
                        "type": "checkbox", "name": "edit_grid_cells", "value": e,
                        "id": e + "_id", "checked": true, "class": "form-control"
                      });

                      domConstruct.place(label, li);
                      domConstruct.place(input, label);
                      domConstruct.place(li, dom.byId("id_edit_grid_cells"));
                    });
                  } else {
                    domConstruct.place("<p>No Cells Assigned</p>", dom.byId("id_edit_grid_cells"));
                  }

                  if (sheet_title === "None") {
                    sheet_title = "";
                  }

                  dom.byId('id_edit_sheet_title').value = sheet_title;

                  Array.forEach(query("#id_edit_discipline input"), function (box) {
                    box.checked = false;
                  });
                  Array.forEach(discipline.split(","), function (e) {
                    Array.some(query("#id_edit_discipline input"), function (input) {
                      if (input.value === e) {
                        input.checked = true;
                      }
                    });
                  });
                  Array.forEach(query("#id_edit_sheet_type input"), function (box) {
                    box.checked = false;
                  });
                  Array.forEach(sheet_type.split(","), function (e) {
                    Array.some(query("#id_edit_sheet_type input"), function (input) {
                      if (input.value === e) {
                        input.checked = true;
                      }
                    });
                  });
                  Array.forEach(query("#id_edit_doc_type input"), function (box) {
                    box.checked = false;
                  });
                  Array.forEach(doc_type.split(","), function (e) {
                    Array.some(query("#id_edit_doc_type input"), function (input) {
                      if (input.value === e) {
                        input.checked = true;
                      }
                    });
                  });

                  if (project_title === "None") {
                    project_title = "";
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

                  Array.forEach(query("#id_edit_airport input"), function (e) {
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
                }
              });
            });
          }

          if (ftype_all) {
            on(ftype_all, 'change', function(evt) {
              console.log(evt);
              evt.preventDefault();

              if (evt.target.checked) {
                // check all of the file type boxes
                Array.forEach([f_nodes, d_nodes, t_nodes, gis_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = true;
                    }
                  });
                });
              } else {
                // uncheck all of the file type boxes
                Array.forEach([f_nodes, d_nodes, t_nodes, gis_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = false;
                    }
                  });
                });
              }
            });
          }

          if (doctype_all) {
            on(doctype_all, 'change', function(evt) {
              console.log(evt);
              evt.preventDefault();

              if (evt.target.checked) {
                // check all of the file type boxes
                Array.forEach([doc_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = true;
                    }
                  });
                });
              } else {
                // uncheck all of the file type boxes
                Array.forEach([doc_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = false;
                    }
                  });
                });
              }
            });
          }

          if (edit_disc_all) {
            on(edit_disc_all, 'change', function(evt) {
              console.log(evt);
              evt.preventDefault();

              if (evt.target.checked) {
                // check all of the file type boxes
                Array.forEach([edit_disc_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = true;
                    }
                  });
                });
              } else {
                // uncheck all of the file type boxes
                Array.forEach([edit_disc_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = false;
                    }
                  });
                });
              }
            });
          }

          if (edit_sheet_all) {
            on(edit_sheet_all, 'change', function(evt) {
              console.log(evt);
              evt.preventDefault();

              if (evt.target.checked) {
                // check all of the file type boxes
                Array.forEach([edit_sheet_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = true;
                    }
                  });
                });
              } else {
                // uncheck all of the file type boxes
                Array.forEach([edit_sheet_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = false;
                    }
                  });
                });
              }
            });
          }

          if (edit_doc_all) {
            on(edit_doc_all, 'change', function(evt) {
              console.log(evt);
              evt.preventDefault();

              if (evt.target.checked) {
                // check all of the file type boxes
                Array.forEach([edit_doc_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = true;
                    }
                  });
                });
              } else {
                // uncheck all of the file type boxes
                Array.forEach([edit_doc_nodes], function(d) {
                  Array.forEach(d, function (i) {
                    {
                      i.checked = false;
                    }
                  });
                });
              }
            });
          }
          // remove the selected grids from the search and edit windows
          self.clearGrid = topic.subscribe("grids/clear", function() {
            if (grid_search_list) {
              grid_search_list.value = "";
            }
            // remove all of the html from the UpdateList
            if (grid_update_list) {
              domConstruct.empty(grid_update_list);
            }
          });

          // add the page number to the filter form, then submit the form
          if (previous_link) {
            on(previous_link, "click", function(evt) {
              evt.preventDefault();
              console.log(filter_form);
              filter_form.submit();
            });
          }

          if (after_link) {
            on(after_link, "click", function(evt) {
              evt.preventDefault();
              console.log(filter_form);
              // get the
              filter_form.submit();
            });
          }

        },

        checkPanel: function (event) {
            // this method controls whether to open or close the left slider panel
            var deferred = new Deferred();
            var target = event.target;
            // if the slider panel is not open, open it.
            if (!domClass.contains(slider_panel, "open")) {
              domClass.replace(slider_panel, "open", "close");
              domClass.remove(event.target, 'btn-clear');
              deferred.resolve(slider_panel);
            } else {
              // the panel is already open; if the button is not clear, close the panel, and make button clear.
              console.log(event.target);
              if (!domClass.contains(event.target, 'btn-clear')) {
                domClass.replace(slider_panel, "close", "open");
                domClass.add(event.target, 'btn-clear');
              } else {
                // the panel is open and the button is clear, keep the panel open, make other buttons clear
                // make this button blue
                Array.forEach([panel_btn, panel_btn2], function (btn) {
                  if (btn !== target) {
                    domClass.add(btn, 'btn-clear');
                  }
                });

                domClass.remove(event.target, 'btn-clear');
              }
              deferred.resolve(slider_panel);
            }

            return deferred.promise;
          }
      });
    });










