
  var levels = {};

  function setLevel(formControlId, id, value) {
    levels[id] = value;

    for (i=-1;i<3;i++) {
      $("#"+id+"-"+i).attr("class", (i<=value) ? "requirement-editor-control requirement-editor-control-active" : "requirement-editor-control");
    }
    $("#"+formControlId).attr("value", value)
    if (value == -1) {
      $("#i"+id).attr("disabled","disabled");
    } else {
      $("#i"+id).removeAttr("disabled");
    }
  };
