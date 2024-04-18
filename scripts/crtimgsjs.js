// create a javascript import file from a directory containing media files (docs, images, texts)
// usage node crtimgsjs.js <media> directory/*, where media is any string
// will create an output (repeat export and import for every file in directory)
//
// import <media>filename from directory/filename.extension
// 
// export default {
//      <media>filename:<media>filename,
//      ...
// }
//
//  
var items = [];

var args = process.argv.slice(2);
const which = args.shift();

args.forEach((value, index) => {
    var name = value.split('/').pop().split('.').shift();
    name = unifyNames(name);
    items.push(name);
    console.log(`import ${which}${name} from '${value}';`);
});

console.log("\nexport default {");
items.forEach(element => {
    console.log(`  '${which}${element}':${which}${element},`);
});

console.log("};\n");

function unifyNames(text) {
    return text.toLowerCase()
        .replace(/[-_\s.]+(.)?/g, (_, c) => c ? c: '');
}

 function camelize(text) {
    const a = text.toLowerCase()
        .replace(/[-_\s.]+(.)?/g, (_, c) => c ? c.toUpperCase() : '');
    return a.substring(0, 1).toLowerCase() + a.substring(1);
}
