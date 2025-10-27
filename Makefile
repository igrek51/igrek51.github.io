setup:
	python3 -m venv venv &&\
	. venv/bin/activate &&\
	pip install --upgrade pip setuptools &&\
	pip install -r requirements.txt

mkdocs-local:
	mkdocs serve

mkdocs-push:
	mkdocs gh-deploy --force --clean --verbose

rubik-svgs:
	curl -L -o docs/assets/misc/rubik/3x_1_white_cross.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=lwlwwwlwllbllblllllrllrllll"
	curl -L -o docs/assets/misc/rubik/3x_2.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=wwwwwwwwwbbblbllllrrrlrllll"
	curl -L -o docs/assets/misc/rubik/3x_3.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=lllllllrllllsrlrrrlbllbsbbb"
	curl -L -o docs/assets/misc/rubik/3x_4_minus.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=lslyyylslllllllllllylllllll"
	curl -L -o docs/assets/misc/rubik/3x_4_l.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=lylyyslsllyllllllllylllllll"
	curl -L -o docs/assets/misc/rubik/3x_4_dot.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=lslsyslsllyllllllllylllllll"
	curl -L -o docs/assets/misc/rubik/3x_5.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=lylyyylyllblrrrrrrlrlbbbbbb"
	curl -L -o docs/assets/misc/rubik/3x_6.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=sysyyysybyrsrrrrrrsbrbbbbbb"
	curl -L -o docs/assets/misc/rubik/3x_7.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&size=200&r=y30x-30&fc=gyyyyybyyrrrrrrrrrobbbbbbbb"

	curl -L -o docs/assets/misc/rubik/4x_edge_parity.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&pzl=4&size=260&r=y30x-30&fc=llllllllllllllllllllglllolllllllllllwbbwybbyllll"
	curl -L -o docs/assets/misc/rubik/4x_oll_parity.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&pzl=4&size=260&r=y30x-30&fc=yssyyyyyyyyyyyyy"
	curl -L -o docs/assets/misc/rubik/4x_pll_parity.svg \
		"https://visualcube.api.cubing.net/visualcube.php?fmt=svg&pzl=4&size=260&r=y30x-30&fc=yyyyyyyyyyyyyyyyrrrrrrrrrrrrrrrrbggb"
