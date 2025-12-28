<?php
$servername = "192.168.101.10:3306";
$username = "root";
$password = "phpts";
$dbname = "mask";
// 创建连接
$conn = new mysqli($servername, $username, $password,$dbname);
 
// 检测连接
if ($conn->connect_error) {
    die("connect db fail: " . $conn->connect_error);
} else{
	// echo "连接成功";
	// $conn->close();
	$type = $_REQUEST["type"];//地址传入参数
	echo $type . "-";
	if ($type == 0 or $type == 1 or $type == 2){
		$date = date("Y-m-d");//日期
		$time = date("H:i:s");//时间
		// $type = 2;//类型
		echo $date;
		echo " ".$time;
		//采用预处理
		$sql = "insert into detail(date,time,type) values(?,?,?)";
		$stmt = $conn->prepare($sql);
		$stmt->bind_param("ssi", $date, $time, $type);//string,string,int
		if ($stmt->execute()){
			echo "success";
			$stmt->close();
		}else{
			echo "fail";
		}
	}else{
		echo "wrong";
	}

	
	

}
// $conn->close();//关闭连接



?>