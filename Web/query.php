<?php
$servername = "192.168.101.10:3306";
$username = "root";
$password = "phpts";
$dbname = "mask";
// 创建连接
$conn = new mysqli($servername, $username, $password,$dbname);
 
// 检测连接
if ($conn->connect_error) {
    die("connect fail: " . $conn->connect_error);
}
else{
	// echo "连接成功";
	// $conn->close();
	$date = $_REQUEST["date"];//地址传入参数
	if ($date == ''){
		$sql = "SELECT * FROM detail order by id";
		$sql2 = "SELECT * FROM byday order by id";
	}else{
		$sql = "SELECT * FROM detail where date = '$date' order by id";
		$sql2 = "SELECT * FROM byday where date = '$date'";
	}
	// $date = date("Y-m-d");//日期
	// $time = date("H:i:s");//时间
	// $type = 2;//类型
	// echo $date;
	// echo " ".$time;
	// echo "<br>";
	// $sql = "SELECT * FROM detail where date = '$date' order by id";
	
	// $data = '';//存详细记录查询到的json数据
	// $array = array();//查到的结果集
	
	//0:各时间段未佩戴口罩,1:各时间段未正确佩戴口罩,2:各时间段正确佩戴口罩
	$arrays = array(
		"0"=>array(),
		"1"=>array(),
		"2"=>array(),
	);
	for ($i = 0; $i < 24; $i++){
		if ($i < 10){
			$temp = 'time' . 0 . $i;//拼接上0,形式为time00，time01....作为JSON键值,纯数字无法取出
			$arrays['0'][$temp] = 0;
			$arrays['1'][$temp] = 0;
			$arrays['2'][$temp] = 0;
		}else{
			$temp = 'time' . $i;//拼接上0
			$arrays['0'][$temp] = 0;
			$arrays['1'][$temp] = 0;
			$arrays['2'][$temp] = 0;
		}

	}
	//每日三类情况累计,初始值为0
	$count_arrays = array(
		"u_mask"=>0,
		"w_mask"=>0,
		"mask"=>0,
	);
	//存储两类数据的数组
	$all_arrays = array(
		"detail_data"=>$arrays,
		"count_data"=>$count_arrays,
	);
	
	// class detail{
	// 	//每一条数据对象
	// 	var $id;
	// 	var $date;
	// 	var $time;
	// 	var $type;
	// 	function __construct($id,$date,$time,$type){
	// 		$this->id = $id;
	// 		$this->date = $date;
	// 		$this->time = $time;
	// 		$this->type = $type;
	// 	}
	// }
	//result暂时保存查询结果
	$result = $conn->query($sql);
	//结果行数大于0
	if ($result->num_rows > 0) {
	    // 输出数据
	    while($row = $result->fetch_assoc()) {
	        // echo "日期: " . $row["date"]. " - 时间: " . $row["time"]. "- 类型" . $row["type"]. "<br>";
			// $detail = new detail($row["id"],$row["date"],$row["time"],$row["type"]);
			// $array[] = $detail;
			$spi_time = 'time' . date("H",strtotime($row["time"]));//时间截取转xxH形式
			// echo $spi_time;
			$arrays[$row["type"]][$spi_time] += 1;
			// echo $arrays[$row["type"]][$spi_time] . "--";	
	    }
		
		$result = $conn->query($sql2);
		$row = $result->fetch_assoc();
		$count_arrays["u_mask"] = $row["u_mask"];
		$count_arrays["w_mask"] = $row["w_mask"];
		$count_arrays["mask"] = $row["mask"];
		
		$data = json_encode($arrays);
		$all_arrays["detail_data"] = $data;
		
		$data = json_encode($count_arrays);
		$all_arrays["count_data"] = $data;
		
		$data = json_encode($all_arrays);
		
		echo $data;
		
		//转JSON对象
		// $date = json_encode($arrays);
		// echo $date;//返回json结果集
	} else {
	    // echo "0 结果";
		// $data = json_encode($arrays);
		// echo $data;
		
		$data = json_encode($arrays);
		$all_arrays["detail_data"] = $data;
		
		$data = json_encode($count_arrays);
		$all_arrays["count_data"] = $data;
		
		$data = json_encode($all_arrays);
		
		echo $data;
		
		
		
		
	}
	//方式二,面向过程$conn=mysqli_connect("localhost","username","password","database");
	// $result = mysqli_query($conn,$sql);
	// echo $result;
	// while($row = mysqli_fetch_array($result)){
	// 	echo "日期: " . $row["date"]. " - 时间: " . $row["time"]. "- 类型" . $row["type"];
	// }
	
	 
}
// $conn->close();//关闭连接

?>