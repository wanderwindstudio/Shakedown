Shader "Shakedown/Spike/Orbit surface"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ LOD_FADE_CROSSFADE
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/LODCrossFade.hlsl"
            struct Input { float4 position:POSITION; float3 normal:NORMAL; half4 colour:COLOR; };
            struct Varying { float4 position:SV_POSITION; half3 normal:TEXCOORD0; half4 colour:COLOR; };
            Varying Vert(Input v) { Varying o; o.position=TransformObjectToHClip(v.position.xyz); o.normal=TransformObjectToWorldNormal(v.normal); o.colour=v.colour; return o; }
            half4 Frag(Varying i):SV_Target
            {
                #ifdef LOD_FADE_CROSSFADE
                    LODFadeCrossFade(i.position);
                #endif
                Light sun=GetMainLight();
                half daylight=dot(normalize(i.normal),sun.direction);
                half terminator=smoothstep(-.008,.008,daylight);
                half3 lighting=lerp(half3(.003,.004,.007),sun.color*max(.08,daylight),terminator);
                return half4(i.colour.rgb*lighting,1);
            }
            ENDHLSL
        }
    }
}
