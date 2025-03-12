var express = require("express");
var server = express();
server.use(express.static("dist"));
server.listen(9090);
console.log("Server Prod started at port 9090");