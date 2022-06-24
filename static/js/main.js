let erasingRemovesErasedObjects = false;
const canvas = this.__canvas = new fabric.Canvas('main_canvas');

function changeAction(target) {
    ['select','text','image','draw','spray'].forEach(action => {
    const t = document.getElementById(action);
    t.classList.remove('btn-large');
    t.classList.remove('blue');
    });
    if(typeof target==='string') target = document.getElementById(target);
    target.classList.add('btn-large');
    target.classList.add('blue');
    switch (target.id) {
    case "select":
        hideControls();
        canvas.isDrawingMode = false;
        break;
    case "text":
        hideControls();
        $('#text_options').removeClass('hide');
        $('#text_options').addClass('show');
        break;
    case "image":
        hideControls();
        $('#image_select').empty()
        getList();
        $('#image_options').removeClass('hide');
        $('#image_options').addClass('show');
        break;
    case "draw":
        hideControls();
        canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
        canvas.freeDrawingBrush.width = 35;
        canvas.isDrawingMode = true;
        break;
    case "spray":
        hideControls();
        canvas.freeDrawingBrush = new fabric.SprayBrush(canvas);
        canvas.freeDrawingBrush.width = 35;
        canvas.isDrawingMode = true;
        break;
    default:
        break;
    }   
}


// Aligns items vertically or horizontally
// GROUP ON SELECTION
canvas.on("selection:updated", function(e) {
	var activeObj = canvas.getActiveObjects();
    if(activeObj.length > 1) {
        
        var groupWidth = e.target.getWidth();
        var groupHeight = e.target.getHeight();
        
        e.target.forEachObject(function(obj) {
            var itemWidth = obj.getBoundingRect().width;
            var itemHeight = obj.getBoundingRect().height;
        
            // OBJECT ALIGNMENT: " Vertical-CENTER "
            // ================================
            $('#objVAlignCenter').click(function() {
                console.log("clicked VAlign");
                obj.set({
                    left: (0 - itemWidth/2),
                    originX: 'left'
                });
                obj.setCoords();
                canvas.renderAll();
            });
            
            // OBJECT ALIGNMENT: " Horizontal-CENTER "
            // ================================
            $('#objHAlignCenter').click(function() {
                console.log("clicked HAlign");
                obj.set({
                    top: (0 - itemHeight/2),
                    originY: 'top'
                });
                obj.setCoords();
                canvas.renderAll();
            });
        });
    }
}); // END OF " SELECTION:CREATED "

// Populates the list of images.
function getList(){
    $.ajax({
        type: 'POST',
        url: '/fill_list',
        success: function(gray_list){
            name_list = gray_list.split("!and!");
            populateList(name_list);
        }
    });
    
}

function populateList(a_name_list){
    
    for (let i = 0; i < a_name_list.length; i++) {
        $('#image_select').append('<option value="">' + a_name_list[i] + '</option>')
    }
}

// Deletes selected items from the canvas
function deleteItems(){
    canvas.getActiveObjects().forEach((obj) => {
        canvas.remove(obj)
    });
}

// Adds a text to the canvas with "Some Text" as the base text
function addText(){
    var text = new fabric.Text("Some Text");
    canvas.add(text);
}

// Changes text of a selected text object
function changeText(){
    var selected = canvas.getActiveObject()
    var selected_type = canvas.getActiveObject().get('type')
    if(selected_type == 'text'){
        var new_text = $('#edited_text').val()
        selected.text = new_text
        canvas.renderAll()
    }
}

// Fills font size and radius select boxes
function fillFontSizes(){
    font_size_html ="";
    for (let i = 1; i < 100; i++) {
        font_size_html = font_size_html + "<option value=" + i + ">" + i + "</option>";    
    }
    $('#font_size').html(font_size_html);
    $('#radius').html(font_size_html);
}

function fillLocation(){
    location_html = "";
    for(let i = 1; i < 361; i++){
        location_html = location_html + "<option value=" + i + ">" + i + "</option>";
    }
    $('#location').html(location_html);
}

// Hides control options for each main object
function hideControls(){
    ['text_options', 'image_options'].forEach(tools => {
        const tool = document.getElementById(tools);
        tool.classList.remove('show');
        tool.classList.add('hide');
    })
}

function addImage(filename){
    fabric.Image.fromURL('static/uploads/grays/' + filename, function(myImg) {
        canvas.add(myImg); 
    });
}


function init() {
    canvas.setOverlayColor("rgba(0,0,0,0)",undefined,{erasable:false});
}

const setDrawableErasableProp = (drawable, value) => {
canvas.get(drawable)?.set({ erasable: value });
changeAction('erase');
};

const setBgImageErasableProp = (input) =>
setDrawableErasableProp("backgroundImage", input.checked);

const setErasingRemovesErasedObjects = (input) =>
(erasingRemovesErasedObjects = input.checked);

const downloadImage = () => {
const ext = "png";
const base64 = canvas.toDataURL({
    format: ext,
    enableRetinaScaling: true
});
const link = document.createElement("a");
link.href = base64;
link.download = `eraser_example.${ext}`;
link.click();
};

const downloadSVG = () => {
const svg = canvas.toSVG();
const a = document.createElement("a");
const blob = new Blob([svg], { type: "image/svg+xml" });
const blobURL = URL.createObjectURL(blob);
a.href = blobURL;
a.download = "eraser_example.svg";
a.click();
URL.revokeObjectURL(blobURL);
};

// Defines the zoom functionality
canvas.on('mouse:wheel', function(opt) {
var delta = opt.e.deltaY;
var zoom = canvas.getZoom();
zoom *= 0.999 ** delta;
if (zoom > 20) zoom = 20;
if (zoom < 0.01) zoom = 0.01;
canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
opt.e.preventDefault();
opt.e.stopPropagation();
});

canvas.on('mouse:down', function(opt) {
    var evt = opt.e;
    if (evt.altKey === true) {
      this.isDragging = true;
      this.selection = false;
      this.lastPosX = evt.clientX;
      this.lastPosY = evt.clientY;
    }
});
canvas.on('mouse:move', function(opt) {
if (this.isDragging) {
    var e = opt.e;
    var vpt = this.viewportTransform;
    vpt[4] += e.clientX - this.lastPosX;
    vpt[5] += e.clientY - this.lastPosY;
    this.requestRenderAll();
    this.lastPosX = e.clientX;
    this.lastPosY = e.clientY;
}
});
canvas.on('mouse:up', function(opt) {
// on mouse up we want to recalculate new interaction
// for all objects, so we call setViewportTransform
this.setViewportTransform(this.viewportTransform);
this.isDragging = false;
this.selection = true;
});
// end zoom

// Fits the canvas to the screen
function fitToDiv(a_canvas){
    var outer_width = $('#main_canvas_div').width();
    var outer_height = $('#image_editing_div').height();
    a_canvas.setWidth(outer_width);
    a_canvas.setHeight(outer_height);
    // hw = outerheight + 'and' + outer_width
    // const request = new XMLHttpRequest;
    // request.open('POST', '/processhw/${JSON.stringify(hw)}')
}

// Shows font input and changes font of selected text when changed
$('#font_input')
    .fontpicker()
    .on('change', function() {
        var selected = canvas.getActiveObject()
        var selected_type = canvas.getActiveObject().get('type')
        if(selected_type == 'text'){
            const font_array = this.value.split(':')
            selected.fontFamily = font_array[0];
            canvas.renderAll()
        }
});

function editObject()
{
    var text = $('#edited_curved_text').val();
    var fName = 'Arial';
    var fSize = +$('#fontSize').val();
    var diameter = +$('#diameter').val();
    var kerning = +$('#kerning').val();
    var flipped = $('#flip').is(':checked');
    var obj = canvas.getActiveObject();

    if (obj) {
        obj.set({
            text: text,
            diameter: +$('#diameter').val(),
            fontSize: fSize,
            fontFamily: fName,
            kerning: kerning,
            flipped: flipped
        });
        canvas.renderAll();
    }
    else {
        obj = new fabric.TextCurved(text, {
            diameter: +$('#diameter').val(),
            fontSize: fSize,
            fontFamily: fName,
            kerning: kerning,
            flipped: flipped,
            left: 50,
            top: 50
        });
        canvas.add(obj);
    }
}

// Update controls
function update(e) {
    var obj = e.target;
    $('#diameter').val(obj.diameter);
    $('#text').val(obj.text);
    $('#fontSize').val(obj.fontSize);
    $('#kerning').val(obj.kerning);
    $('#flip').prop('checked', obj.flipped);
}

canvas.on({
    'object:selected': function(e) {
        update(e);
    },
    'selection:updated': function(e) {
        update(e);
    }
})

init();
fitToDiv(canvas);
fillFontSizes()
fillLocation()
