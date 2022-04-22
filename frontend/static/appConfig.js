const hosts={
	"production":window.location.hostname,
	"development":"10.88.44.53",
	// "development": "10.88.44.53",
	// development:"10.88.45.235"
};
let host=hosts[env];
// var port=":8080";
var port=":9992"
var configPort=":8888";
let msPrefix={
	socketUrl:'ws://'+host+port+'/portal/ws',
	sms:port+"/ms-sms",
	base:port+"",
	config:configPort,
	eureka:port+"/dm-eureka-server",
	psem:port+"/ms-psem",
    autopolling:port+"/MS-AUTO-POLLING",
	autoapppolling:port+"/MS-AUTO-APP-POLLING",
	autoDeployer:port+"/MS-AUTO-DEPLOYER",
	autochange:port+"/MS-AUTO-CHANGE",
	automation:port+"/ms-automation"
}
let validateRules={
	inputMaxLength:100,
	textMaxLength:1000
}


let versions={
	"name":"aom",//如果是能力开放平台，请设置成"openplat"；如果是自动化运维门户，请设置为"octopusplat"
	"aom":{
		logo:"logo-pbdp.png",
		menus:"routers-aom",
		// loginBg:"login-bg.png",
		loginBg:"bgdark.png",
		title:"Linux采集工具"
	}
}

var inputMap = {"input":"文本框","textarea":"文本域","number":"数值","date":"日期","datetime":"日期时间","checkbox":"复选框","dict-checkbox":"字典复选框","radio":"单选框","dict-tree":"字典树","select":"下拉选择框",
				"dict-select":"字典下拉单选","dict-multiselect":"字典下拉多选","boolean":"逻辑选择","data-item":"关联单个配置项","data-item-multi":"关联多配置项","org-select":"机构选择框"};
var row24 = ['textarea','checkbox','dict-checkbox','radio','data-item','data-item-multi'];
var inputTypes = [];
Object.keys(inputMap).forEach(item=>{
	var rowColumns = 6;
	if(row24.includes(item)){
		rowColumns=24;
	}
	inputTypes.push({label:inputMap[item],value:item,rows:rowColumns});
})

var dataTypes = ['String'];

/**
 * 基于自动化运维门户或者能力开放平台进行定制的配置属性值
 * @added by steven at 2020/03/10
 */
let customs = { 
	flag: false,   // 默认应为false即正常产品的UI呈现，若为true则会以下面配置的客户名称UI呈现
	name:'hisense', //定制的客户名称
}

window.globalConfig = {
	msPrefix:msPrefix,
	versions:versions,
	inputTypes : inputTypes,
	dataTypes : dataTypes,
	apiUrl: window.location.protocol+"//"+host,
	appName: versions[versions["name"]].title,
	rules:validateRules,
	customs: customs
}
document.title=window.globalConfig.appName;
