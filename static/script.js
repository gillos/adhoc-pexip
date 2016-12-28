$.getJSON("http://adhoc-pexip.lan.kth.se:5000/wait",function(data){
   $("#bla").html('');
   $("#bla").append(data.Done);
});
