<?php
$servername = "192.168.101.10:3306";
$username = "root";
$password = "phpts";
$dbname = "mask";
// 创建连接
$conn = new mysqli($servername, $username, $password,$dbname);
 
// 检测连接
if ($conn->connect_error) {
    die("连接失败: " . $conn->connect_error);
} else{
	 // echo "连接成功";
	// $conn->close();
	// $date = $_REQUEST["date"];//地址传入参数
	// if ($date == ''){
	// 	$sql = "SELECT * FROM detail order by id";
	// }else{
	// 	$sql = "SELECT * FROM detail where date = '$date' order by id";
	// }
	// $date = date("Y-m-d");//日期
	$time = date("H:i:s");//时间
	// $type = 2;//类型
	// echo $date;
	// echo " ".$time;
	// echo "<br>";
	$sql = "SELECT date FROM byday order by date DESC LIMIT 10";
	//方式一
	$result = $conn->query($sql);
	if ($result->num_rows > 0) {
	    // 输出数据
		$list = [];
	    while($row = $result->fetch_assoc()) {
	        $list[] = $row;
	    }
		
	echo '<select style="height:30px;border: dashed" name="lists" onchange="getData(this.value)">';
	echo '<option>';
	echo '' . 请选择日期 . '';
	echo '</option>'; 
		foreach($list as $incuarr){
		    echo '<option>';
		    echo '' . $incuarr['date'] . '';
		    echo '</option>'; 
		}
	echo '</select>';

	} else {
	    echo "0 结果";
	}
	 
}
// $conn->close();//关闭连接

?>