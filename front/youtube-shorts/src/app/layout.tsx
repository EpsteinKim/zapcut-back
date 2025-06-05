'use client';

import './globals.css';
import { ThemeProvider } from '@material-tailwind/react';
import React from 'react';

export default function RootLayout({
	children
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html>
			<body>
				<ThemeProvider>
					{ children }
				</ThemeProvider>
			</body>
		</html>
	);
}
