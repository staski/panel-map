import images from './images';
import docs from './docs';
import texts from './texts';

var panelAreas = [
{
	name:	'demodevice1',
	shape:	'rect',
	coords:	[353,191,525,353],
	id:	'0',
	img:	images.imgdemodevice1,
	title:	texts.titledemodevice1,
	href:	docs.docdemodevice1,
	text:	texts.textdemodevice1
},
{
	name:	'demodevice2',
	shape:	'rect',
	coords:	[897,64,1193,206],
	id:	'1',
	img:	images.imgdemodevice2,
	title:	texts.titledemodevice2,
	href:	docs.docdemodevice2,
	text:	texts.textdemodevice2
}, 
];

export {
	panelAreas,
};