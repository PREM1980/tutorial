 $(document).ready(function() {


     curr_date = new Date()

     curr_date_3 = new Date()
     curr_date_3.setMonth(curr_date_3.getMonth() - 3)

     $('#datepicker').datetimepicker({
         value: curr_date,
         step: 10
     });

     $("#query_datepicker_start").datepicker({
         value: curr_date_3,
         step: 10
     });

     $(function() {
         $("#zipcode").multiselect({
             height: 150,
             show: ['slide', 200],
             hide: ['slide', 200],
             noneSelectedText: 'Select Zipcodes'
         }).multiselectfilter();
     });


     // function get_pgs(pg_object) {
     //     pg = []
     //     a = $(pg_object).multiselect("getChecked")
     //     for (index = 0; index < a.length; ++index) {
     //         console.log("select value == ", a[index].value)
     //         pg.push(a[index].value)

     //     }
     //     multiselect_widget_length = $(pg_object).multiselect("widget").find('.ui-multiselect-checkboxes li').length

     //     console.log('multiselect_widget_length == ', multiselect_widget_length)
     //     console.log('pg.length ==', pg.length)

     //     if ((multiselect_widget_length == pg.length) && (multiselect_widget_length != 0)) {
     //         pg = []
     //         pg.push('ALL')
     //     }
     //     console.log('return pg ==', pg)
     //     return pg;

     // }

     $('#upload').click(function(event) {
         event.preventDefault();
         event.stopPropagation();

         if (($('#division').val().length == 0) || ($('#division').val() == 'Division')) {
             alert('Select a division')
         } else if ($('#peergroup :selected').length == 0) {
             alert('Select a peergroup')
         } else if ($('#duration').val() == 'Duration (in minutes)') {
             alert('Pick Duration value')
         } else if ($('#errorcount').val() == 'Error Count') {
             alert('Pick ErrorCount value')
         } else if ($('#cause').val() == 'Outage Caused') {
             alert('Pick OutageCaused value')
         } else if ($('#subcause').val() == 'System Caused') {
             alert('Pick SystemCaused value')
         } else if ($('#ticket_no').val().length == 0) {
             alert('Enter a valid ticket number')
         } else if ($('#radio1').is(':not(:checked)') && $('#radio2').is(':not(:checked)')) {
             alert('Select JIRA/TTS ticket')
         } else {
             console.log("peergroup == ", $('#peergroup').multiselect("getChecked"))
             pg = get_pgs('#peergroup')

             data = {
                 'date': $('#datepicker').val(),
                 'division': $('#division').val(),
                 'pg': pg,
                 'duration': $('#duration').val(),
                 'error_count': $('#errorcount').val(),
                 'ticket_num': $('#ticket_no').val(),
                 'outage_caused': $('#cause').val(),
                 'system_caused': $('#subcause').val(),
                 'addt_notes': $('#additional_notes').val(),
                 'ticket_type': $('input[name=tkt-radio]:checked').val()
             }
             console.log('data_table insert data == ', data)

             $.ajax({
                 type: "POST",
                 url: '/post-ticket-data',
                 data: data,
                 success: function(result) {
                     console.log('post update result == ', result.status)

                     if (result.status != 'success') {
                         alert(result.status)
                     } else {
                         alert("You're stored in our DB!! Playaround!!")
                         load_datatable('Y')
                     }
                 },
             });

         }

     });



     $('#radio_division').click(function() {
         if ($('#radio_division').is(':checked')) {
             $('#divisions').show()
             $('#divisions_header').show()
             $("#radio_national").removeAttr("checked");
         }
     });

     $('#radio_national').click(function() {
         if ($('#radio_national').is(':checked')) {
             $('#divisions').hide()
             $("#radio_division").removeAttr("checked");
         }
     });

     $(function() {
         $("#dialog_pg_select").dialog({
             maxWidth: 800,
             maxHeight: 1000,
             width: 500,
             height: 500,
             modal: true,
             autoOpen: false,

         })

     });



     $(function() {
         $("#dialog").dialog({
             maxWidth: 800,
             maxHeight: 1000,
             width: 500,
             height: 500,
             modal: true,
             autoOpen: false,
             show: {
                 effect: "explode",
                 duration: 100
             },
             hide: {
                 effect: "explode",
                 duration: 100
             },
             buttons: {
                 "Update": function() {
                     data = {}
                     pg = get_pgs('#row_peergroup')
                     data = {
                         'division': $('#row_division').val(),
                         'pg': pg,
                         'duration': $('#row_duration').val(),
                         'error_count': $('#row_error_count').val(),
                         'outage_caused': $('#row_cause').val(),
                         'system_caused': $('#row_system_cause').val(),
                         'addt_notes': $('#dialog_addt_notes').html(),
                         'ticket_num': $('#dialog_ticket_num').html(),
                         'ticket_type': $('#dialog_ticket_type').html(),
                         'update': 'N',
                         //'initial': initial
                     }

                     console.log('update data == ', data)
                     $.ajax({
                         url: '/update_ticket_data',
                         type: 'POST',
                         data: data,
                         success: function(result) {

                             if (result.status != 'success') {
                                 alert("Row Update Failed!! Contact Support")
                             } else {
                                 alert("Row Updated!! Playaround!!")
                                 $('#dialog').dialog("close");
                                 load_datatable('Y')

                             }
                         },
                         error: function(msg) {
                             alert("Call to Update ticket failed!! Contact Support!!")
                         }
                     })
                 },
                 "Cancel": function() {
                     $(this).dialog("close");
                 }
             }


         })
     });


     $("#division").change(function() {
         $("#dialog-pg").dialog("open");
     });


     $("#opener").click(function() {
         $("#dialog").dialog("open");
     });



     $('#query').click(function() {
         load_datatable('N')
     })

     var load_datatable = function(initial) {
         data = {}
         pg = []
         if (initial == 'N') {
             pg = get_pgs('#query_peergroup')
         }

         data = {
             'start_date_s': $('#query_datepicker_start').val(),
             'start_date_e': $('#query_datepicker_start_end').val(),
             'end_date_s': $('#query_datepicker_end').val(),
             'end_date_e': $('#query_datepicker_end_end').val(),
             'ticket_num': $('#query_ticket_no').val(),
             'division': $('#query_division').val(),
             'pg': pg,
             //'error_count': $('#duration').val(),
             'outage_caused': $('#query_cause').val(),
             'system_caused': $('#query_subcause').val(),
             'addt_notes': $('#query_addt_notes').html(),
             'initial': initial
         }

         console.log('data_table data == ', data)

         $.ajax({
             url: '/get_ticket_data',
             type: 'POST',
             data: data,
             success: create_tickets,
             error: function(msg) {
                 alert("Call to searchproduct failed")
             }
         })
     }


     load_datatable('Y')

     function create_tickets(jsondata) {
         transactiondata = jsondata
         console.log('transactiondata length == ', transactiondata.results.length)
         $("<div class='CSSTableGenerator'></div>").appendTo("#ticket_list");
         $('#pagination').pagination({
             items: transactiondata.results.length,
             itemsOnPage: 12,
             onInit: redrawData,
             onPageClick: redrawData,
             cssStyle: 'light-theme'
         });
     }

     function redrawData(pageNumber, event) {
         //console.log('jsondata = ' + JSON.stringify(transactiondata.results))
         //console.log('pageNumber = ' + pageNumber)
         transactiondata_results = transactiondata.results
         if (pageNumber) {
             if (pageNumber == 1) {
                 slicedata = transactiondata_results.slice(0, 12)
             } else {
                 //console.log('inside transactiondata = ' + transactiondata_results)
                 slicedata = transactiondata_results.slice(pageNumber * 5,
                     Math.min((pageNumber + 1) * 5, transactiondata_results.length));
                 //console.log('start', ((pageNumber - 1) * 12 + 1))
                 //console.log('end', 12 * pageNumber + 1)
                 slicedata = transactiondata_results.slice(((pageNumber - 1) * 12 + 1), 12 * pageNumber + 1)
                     //console.log('inside slicdata == ', slicedata)
             }
         } else {
             slicedata = transactiondata_results.slice(0, 12)
                 //console.log('sliced transactiondata = ' + JSON.stringify(transactiondata))
         }

         $(".CSSTableGenerator").empty()

         $("<table id='ticket-table' style='table-layout:fixed; width:100%'> </table>").appendTo('.CSSTableGenerator')
         $('#ticket-table').append('<tr><td style="display:none">id</td><td>Create Date</td><td>End Date</td><td>Ticket#</td><td> Division </td> <td>PeerGroup</td> <td>Duration</td><td>Error Count</td><td>Outage Cause</td><td>System Caused</td><td>Addt Notes</td><td></td></tr>');

         slicedata.forEach(function(e, i, a) {
             var obj = e;
             //console.log('obj == ', obj)
             //$('#ticket-table').append('<tr><td style="display:none">' + obj.ticket_id + '</td><td>' + obj.created_dt + '</td><td>' + obj.ticket_num + '</td> <td>' + obj.division + '</td><td>' + obj.pg + '</td> <td>' + obj.duration + '</td><td>' + obj.error_count + '</td><td>' + obj.outage_caused + '</td><td>' + obj.system_caused + '</td><td>' + obj.addt_notes + '</td><td><button id="edit' + i + '"">edit</button></td></tr>');
             $('#ticket-table').append('<tr><td style="display:none">' + obj.ticket_type + '</td><td>' + obj.created_dt + '</td><td>' + obj.created_dt + '</td><td>' + obj.ticket_num + '</td> <td>' + obj.division + '</td><td>  <select id="table_pg' + i + '""> </select>  </td> <td>' + obj.duration + '</td><td>' + obj.error_count + '</td><td>' + obj.outage_caused + '</td><td>' + obj.system_caused + '</td><td>' + obj.addt_notes + '</td><td><button id="edit' + i + '"">edit</button><button id="end' + i + '"">end</button></td></tr>');
             console.log('obj == ', obj.pg)
             for (j = 0; j < obj.pg.length; j++) {
                 $('#table_pg' + i).append($('<option>', {
                     value: obj.pg[j],
                     text: obj.pg[j]
                 }))
             }


         })

         $('[id^=end]').click(function() {
             data = {}
             row = $(this).parent().parent()
             ticket_num = row.find("td:nth-child(4)").html()
             data = {
                 'ticket_num': ticket_num,
                 'update': 'Y',
             }

             console.log('update data == ', data)
             $.ajax({
                 url: '/update_ticket_data',
                 type: 'POST',
                 data: data,
                 success: function(result) {

                     if (result.status != 'success') {
                         alert("Row End date Failed!! Contact Support")
                     } else {
                         alert("Row End-Dated!! Playaround!!")
                     }
                 },
                 error: function(msg) {
                     alert("Call to End date ticket failed!! Contact Support!!")
                 }
             })
         })

         $('[id^=edit]').click(function() {
             var id = $(this).attr('id');
             row = $(this).parent().parent()

             console.log($(this).parent().parent().find("td:first").html())

             ticket_type = row.find("td:first").html()
             created_dt = row.find("td:nth-child(3)").html()
             ticket_num = row.find("td:nth-child(4)").html()
             division = row.find("td:nth-child(5)").html()
             pg = row.find("td:nth-child(6), select")
             duration = row.find("td:nth-child(7)").html()
             error_count = row.find("td:nth-child(8)").html()
             outage_caused = row.find("td:nth-child(9)").html()
             system_caused = row.find("td:nth-child(10)").html()
             addt_notes = row.find("td:nth-child(11)").html()
             console.log("dialog duration == ", duration)
             console.log("dialog created_dt == ", created_dt)
             console.log("dialog error_count == ", error_count)
             console.log("dialog outage_caused == ", outage_caused)

             $("#dialog_created_dt").html(created_dt)
             $("#dialog_ticket_num").html(ticket_num)
             $("#dialog_ticket_type").html(ticket_type)
             $("#dialog_division select").val(division)
             division = $("#row_division")[0]

             var pg_cds_array = []
             $(pg).find('option').each(function(i, selected) {
                 pg_cds_array[i] = $(selected).val();
             });

             getval(division, 'setting', pg_cds_array)

             $("#dialog_duration select").val(duration)
             $("#dialog_error_count select").val(error_count)
             $("#dialog_outage_caused select").val(outage_caused)
             $("#dialog_system_caused select").val(system_caused)
             $("#dialog_addt_notes").html(addt_notes)
             $("#dialog").dialog("open");

             //Very important 
             //Don't remove this piece of code, if its removed you will unable to edit filter text box
             //http://stackoverflow.com/questions/16683512/jquery-ui-multiselect-widget-search-filter-not-receiving-focus-when-in-a-jquery
             if ($.ui && $.ui.dialog && $.ui.dialog.prototype._allowInteraction) {
                 var ui_dialog_interaction = $.ui.dialog.prototype._allowInteraction;
                 $.ui.dialog.prototype._allowInteraction = function(e) {
                     if ($(e.target).closest('.ui-multiselect-filter input').length) return true;
                     return ui_dialog_interaction.apply(this, arguments);
                 };
             }


             //load_datatable('N')
         })
     }
 })
