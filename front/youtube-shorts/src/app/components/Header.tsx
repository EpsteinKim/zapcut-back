'use client';
import { Button, Navbar, Typography } from '@material-tailwind/react';
import { useState } from 'react';

export const Header = () => {
	const [commonProps, _] = useState<string[]>(['cursor-pointer']);
	return (
		<Navbar className={ 'sticky top-0 z-50 bg-gradient-to-t from-purple-900 to-gray-800 border-0 flex justify-between' }>
			<Typography variant='h4' className='text-white/90 font-bold'>
				Youtube Short AI
			</Typography>
			<div className={ 'flex items-center space-x-6' }>
				<Typography className={ commonProps.join(' ') }>기능</Typography>
				<Typography className={ commonProps.join(' ') }>가격</Typography>
				<Typography className={ commonProps.join(' ') }>도구</Typography>
				<Button size={ 'sm' } variant={ 'outlined' } ripple={ false } className={ commonProps.join(' ') }>로그인</Button>
			</div>
		</Navbar>
	);
};