let params = new URLSearchParams(document.location.search);
let placeId = params.get("placeId");
let gameInstanceId = params.get("gameInstanceId");

location.href = "roblox://experiences/start?placeId=" + placeId + "&gameInstanceId=" + gameInstanceId