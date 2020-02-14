function uuidv4() {
    //https://stackoverflow.com/a/2117523/1819160
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

/* Common initialization code. */
var partialReadyFunction = function(root) {
    /** This is different from .ready() in that this one will be called
     *  also by Intercooler.ready on partial loads.
     */
    // Enable sidebar (layouts/_left_menu.html), when available
    $('.ui.dropdown').dropdown();
    $('.accordion').accordion();

    $('.autotab').each(function() {
        /* We put .autotab when doing tabs so they get initialized here.
            If the parent.parent of the autotab has no id, we invent one
            so we can use it for the context below.
            TODO: Get the path to the tabs, so it can be used as context
                without the id magic.
         */
        // see if the parent has an id set for using as tab context.
        var tabContext = $(this).parent().parent().attr('id');
        if (tabContext === undefined) {
            $(this).parent().parent().attr('id', uuidv4());
            tabContext = $(this).parent().parent().attr('id');
        }
        $(this).find('.item').tab({
            context: '#' + tabContext,
        });
    })
};

$(document).ready(function() {
    $('#sidebar-menu')
        .sidebar('setting', 'transition', 'overlay')
        // Enable menu button on top (_top_menu.html), when available.
        .sidebar('attach events', '#sidebar-menu-toggler');

    partialReadyFunction($(":root"));
});

Intercooler.ready(partialReadyFunction);
