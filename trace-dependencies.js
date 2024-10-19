const { nodeFileTrace } = require('@vercel/nft');

async function getDependencies() {
    const { fileList } = await nodeFileTrace([require.resolve('./main.py')], {
        base: process.cwd(),
    });
    console.log(fileList);
}

getDependencies();
