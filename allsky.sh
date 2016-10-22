#!/bin/bash
result=$(lsusb | grep -e "ID 1278:0509 Starlight Xpress")

if [ $? -ne 0 ]; then
        #printf "Device is unplugged\n"
        exit
else
	#source /home/pi/env/allsky/bin/activate
	python /home/pi/pyOculus/pyOculus/snapper.py
	convert -quality 90% -resize 75% /home/pi/images/lastest.png /home/pi/images/latest.jpg
	#/usr/local/bin/s3cmd -c /home/pi/.s3cfg --no-progress sync images/*.jpg s3://www.zemogle.uk/allsky/
	#/usr/local/bin/s3cmd -c /home/pi/.s3cfg --no-progress sync images/*.json s3://www.zemogle.uk/allsky/

	# Next make a list of all .png files created in the last 24 hours & Make a movie out of them
	find /home/pi/images/20*.png -type f -cmin -1440 -exec cat {} \; | /usr/local/bin/ffmpeg -f image2pipe -framerate 5 -i - -s 696x520 -vcodec libx264  -pix_fmt yuv420p /tmp/latest.mp4 -y
	#/usr/local/bin/s3cmd -c /home/pi/.s3cfg --no-progress sync /home/pi/latest.mp4 s3://www.zemogle.uk/allsky/
	mv /tmp/latest.mp4 /home/pi/images/latest_$(date +%F).mp4
	#/usr/local/bin/s3cmd -c /home/pi/.s3cfg --no-progress sync /home/pi/images/*_.mp4 s3://www.zemogle.uk/allsky/archive/
fi
