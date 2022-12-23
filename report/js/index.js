function show_it_by_id(tbl_id) {
  if($(tbl_id).hasClass("hide")) {
    $(tbl_id).removeClass("hide");
  }else {
    $(tbl_id).addClass("hide");
  }
}

function show_it(idx) {
    tbl_id = "#tbl_content"+idx  
    show_it_by_id(tbl_id)
}